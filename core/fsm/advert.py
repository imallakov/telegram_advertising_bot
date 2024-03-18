from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message, CallbackQuery

from bot import get_chat_by_username_from_telegram, get_member_count, bot_edit_message_text_in_chat, \
    bot_delete_message_from_chat
from core.api.dadata_fns import get_organisation_by_inn
from core.database.requests import create_advert
from core.handlers.apshed import bot_notify_moderators
from core.handlers.basic import cmd_start
from core.keyboards.inline_keyboards import chats_choice, chosen_chat, inline_calendar_year_choice, \
    inline_calendar_day_choice, inline_calendar_month_choice, tariff_choice, confirm_data, surely_decline_keyboard, \
    markirovka_reklamy, check_organisation_name_by_inn
from core.keyboards.callbackdata import ChatsCallback, CalendarCallback, TariffCallback

storage = RedisStorage.from_url("redis://localhost:6379/0")

advert_fsm_router = Router()


class FSMAdvert(StatesGroup):
    choose_chat = State()
    choose_date = State()
    choose_tarif = State()
    send_media = State()
    send_text = State()
    check_data = State()
    decline_note = State()
    ask_ad_labeling = State()
    organization_inn = State()
    check_organisation_name = State()
    organization_name = State()
    organization_erid = State()


@advert_fsm_router.message(StateFilter(FSMAdvert.decline_note))
async def receive_decline_note(message: Message, state: FSMContext):
    user_data = await state.get_data()
    query_message_id = user_data['query_message_id']
    sent_message_id = user_data['sent_message_id']
    advert_id = user_data['advert_id']
    await state.update_data(note=message.text)
    await message.answer(text=f'Причина отказа:\n{message.text}', reply_markup=await surely_decline_keyboard(advert_id))
    await bot_delete_message_from_chat(chat_id=message.chat.id, message_id=query_message_id)
    await bot_delete_message_from_chat(chat_id=message.chat.id, message_id=sent_message_id)
    await message.delete()


@advert_fsm_router.message(F.text.lower() == "отмена",
                           StateFilter(FSMAdvert.choose_date, FSMAdvert.choose_chat, FSMAdvert.choose_tarif,
                                       FSMAdvert.send_text, FSMAdvert.check_data))
async def cancel_state(message: Message, state: FSMContext):
    user_data = await state.get_data()
    await bot_edit_message_text_in_chat(message.from_user.id, user_data['message_id'],
                                        new_text='Вы отменили размещение рекламы...')
    await message.delete()
    await state.clear()
    await state.update_data({})
    await cmd_start(message, None)


@advert_fsm_router.callback_query(ChatsCallback.filter(F.event == "back_to_chat_choice"),
                                  StateFilter(FSMAdvert.choose_chat))
@advert_fsm_router.callback_query(ChatsCallback.filter(F.event == "index"), ~StateFilter(default_state))
async def chat_choice(query: CallbackQuery, callback_data: ChatsCallback):
    index: int = callback_data.param
    await query.message.edit_text(text='Пожалуйста, выберите чат/канал для размещение рекламы:',
                                  reply_markup=await chats_choice(index))
    await query.answer()


@advert_fsm_router.callback_query(ChatsCallback.filter(F.event == "chat_id"), StateFilter(FSMAdvert.choose_chat))
async def chat_choice(query: CallbackQuery, callback_data: ChatsCallback, state: FSMContext):
    chat_id: int = callback_data.param
    chat = await get_chat_by_username_from_telegram(chat_id)
    member_count = await get_member_count(chat_id)
    await state.update_data(chat_title=chat.title)
    await query.message.edit_text(
        text=f'Вы выбрали {chat.title}\nКоличество подписчиков: {member_count}\nЧтобы перейти чату/каналу '
             f'воспользуйтесь кнопкой внизу👇🏻',
        reply_markup=await chosen_chat(chat.username, chat_id))
    await query.answer()


@advert_fsm_router.callback_query(ChatsCallback.filter(F.event == "surely_chosen_chat"),
                                  StateFilter(FSMAdvert.choose_chat))
async def process_name_sent(query: CallbackQuery, callback_data: ChatsCallback, state: FSMContext):
    await state.update_data(chat_id=callback_data.param)
    await state.set_state(FSMAdvert.choose_date)
    await calendar_day_choice(query, CalendarCallback(event='start_choosing', year=datetime.today().year,
                                                      month=datetime.today().month), state)
    await query.answer()


@advert_fsm_router.callback_query(CalendarCallback.filter(F.event == "new_date"), StateFilter(FSMAdvert.choose_date))
async def calendar_day_choice(query: CallbackQuery, callback_data: CalendarCallback, state: FSMContext):
    year = callback_data.year
    month = callback_data.month
    user_data = await state.get_data()
    if callback_data.event == "new_date":
        old_reply = query.message.reply_markup.inline_keyboard
        old_year = old_reply[0][1].text
        old_month = old_reply[1][1].text
        reply = await inline_calendar_day_choice(user_data['chat_id'], year, month)
        new_reply = reply.inline_keyboard
        new_year = new_reply[0][1].text
        new_month = new_reply[1][1].text
    if callback_data.event == 'new_date' and not (
            old_year == new_year and old_month == new_month) or callback_data.event == "start_choosing":
        await query.message.edit_text(text='Выберите дату размещения рекламы',
                                      reply_markup=await inline_calendar_day_choice(user_data['chat_id'], year, month))
    await query.answer()


@advert_fsm_router.callback_query(CalendarCallback.filter(F.event == "choose_year"), StateFilter(FSMAdvert.choose_date))
async def calendar_year_choice(query: CallbackQuery, callback_data: CalendarCallback):
    month = callback_data.month
    await query.message.edit_text(text='Выберите год:', reply_markup=await inline_calendar_year_choice(month))
    await query.answer()


@advert_fsm_router.callback_query(CalendarCallback.filter(F.event == "choose_month"),
                                  StateFilter(FSMAdvert.choose_date))
async def calendar_month_choice(query: CallbackQuery, callback_data: CalendarCallback):
    year = callback_data.year
    await query.message.edit_text(text='Выберите месяц:', reply_markup=await inline_calendar_month_choice(year))
    await query.answer()


@advert_fsm_router.callback_query(CalendarCallback.filter(F.event == "choose_another"),
                                  StateFilter(FSMAdvert.choose_date))
async def choose_another(query: CallbackQuery):
    await query.answer(text='Выберите СВОБОДНУЮ и НЕ ПРОШЕДШУЮ дату!', show_alert=True)


@advert_fsm_router.callback_query(CalendarCallback.filter(F.event == "chosen_date"), StateFilter(FSMAdvert.choose_date))
async def chosen_date_choice(query: CallbackQuery, callback_data: CalendarCallback, state: FSMContext):
    month = callback_data.month
    year = callback_data.year
    day = callback_data.day
    await state.update_data(year=year, month=month, day=day)
    await state.set_state(FSMAdvert.choose_tarif)
    user_data = await state.get_data()
    await query.message.edit_text(text=f'Выберите тариф:', reply_markup=await tariff_choice(user_data['chat_id']))
    await query.answer()


@advert_fsm_router.callback_query(TariffCallback.filter(F.event == "chosen_tariff"),
                                  StateFilter(FSMAdvert.choose_tarif))
async def chosen_tariff_choice(query: CallbackQuery, callback_data: TariffCallback, state: FSMContext):
    tariff_id = callback_data.tariff_id
    days = callback_data.days
    price = callback_data.price
    await state.update_data(tariff_id=tariff_id, days=days, price=price)
    await state.set_state(FSMAdvert.send_media)
    await query.message.edit_text(
        text=f'ШАГ 1. отправьте ТОЛЬКО ОДНО фото/видео в сжатом виде а не как файл',
        reply_markup=None)
    await query.answer()


@advert_fsm_router.message(StateFilter(FSMAdvert.send_media))
async def send_advert_media(message: Message, state: FSMContext):
    if not (message.photo is None and message.video is None):
        type = ''
        media_id = ''
        if message.photo is not None:
            type = 'photo'
            media_id = message.photo[-1].file_id
        elif message.video is not None:
            type = 'video'
            media_id = message.video.file_id
        await state.update_data(media_type=type, media_id=media_id)
        await state.set_state(FSMAdvert.send_text)
        await message.answer('Отправленный мадифайл сохранен!\nШАГ 2. Отправьте пожалуйста текст рекламного поста:')
    else:
        await message.answer('Неправильный тип медиафайла.\nОтправьте ТОЛЬКО ОДНО ФОТО ИЛИ ВИДЕО пожалуйста '
                             'В СЖАТОМ ВИДЕ А НЕ КАК ФАЙЛ!')


@advert_fsm_router.message(StateFilter(FSMAdvert.send_text))
async def send_advert_post(message: Message, state: FSMContext):
    await state.update_data(text=message.text, user_id=message.from_user.id)
    await state.set_state(FSMAdvert.ask_ad_labeling)
    await message.answer(text='Вы маркируете свою рекламу?', reply_markup=await markirovka_reklamy())


@advert_fsm_router.callback_query(F.data == 'net_markirovki', StateFilter(FSMAdvert.ask_ad_labeling))
async def bez_markirovki(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await state.set_state(FSMAdvert.check_data)
    user_data = await state.get_data()
    media_type = user_data['media_type']
    media_caption = user_data['text'] + '\n\n\n⬆️Вот так будет выглядеть ваше обявление!⬆️'
    if media_type == 'photo':
        await query.message.bot.send_photo(chat_id=query.message.chat.id, photo=user_data['media_id'],
                                           caption=media_caption, reply_markup=await confirm_data())
    else:
        await query.message.bot.send_video(chat_id=query.message.chat.id, video=user_data['media_id'],
                                           caption=media_caption, reply_markup=await confirm_data())
    await query.answer()


@advert_fsm_router.callback_query(F.data == 'markirovka', StateFilter(FSMAdvert.ask_ad_labeling))
async def markirovka(query: CallbackQuery, state: FSMContext):
    await state.set_state(FSMAdvert.organization_inn)
    await query.message.bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                                      message_id=query.message.message_id, reply_markup=None)
    await query.message.edit_text(text='Отправьте пожалуйста ИНН вашей организации:')
    await query.answer()


@advert_fsm_router.message(StateFilter(FSMAdvert.organization_name))
async def receive_organization_name(message: Message, state: FSMContext):
    organization_name = message.text
    await state.update_data(organization_name=organization_name)
    await state.set_state(FSMAdvert.organization_erid)
    await message.answer(text='Отправьте пожалуйста erid токен вашей организации:')


@advert_fsm_router.message(StateFilter(FSMAdvert.organization_inn))
async def search_organization_name(message: Message, state: FSMContext):
    organization_inn = message.text
    organisation = await get_organisation_by_inn(inn=organization_inn)
    msg_text: str
    is_found: bool = True
    if organisation is None:
        msg_text = "Мы не смогли найти вашу организацию по ИНН!"
        is_found = False
    else:
        msg_text = (f"Результат поиска организации по ИНН:\n"
                    f"Ваша организация:\n{organisation['value']}")
    await state.update_data(organization_inn=organization_inn)
    if is_found:
        await state.update_data(organization_name=organisation['value'])
    await state.set_state(FSMAdvert.check_organisation_name)
    await message.answer(text=msg_text, reply_markup=await check_organisation_name_by_inn(is_found))


@advert_fsm_router.callback_query(F.data == 'enter_inn_again', StateFilter(FSMAdvert.check_organisation_name))
async def enter_inn_again_query(query: CallbackQuery, state: FSMContext):
    await state.set_state(FSMAdvert.organization_inn)
    await query.message.bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                                      message_id=query.message.message_id, reply_markup=None)
    await query.message.edit_text(text='Отправьте пожалуйста ИНН вашей организации:')
    await query.answer()


@advert_fsm_router.callback_query(F.data == 'enter_org_name', StateFilter(FSMAdvert.check_organisation_name))
async def enter_organization_name(query: CallbackQuery, state: FSMContext):
    await state.set_state(FSMAdvert.organization_name)
    await query.message.bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                                      message_id=query.message.message_id, reply_markup=None)
    await query.message.edit_text(text='Отправьте пожалуйста название вашей организации:')
    await query.answer()


@advert_fsm_router.callback_query(F.data == 'correct_organisation_name', StateFilter(FSMAdvert.check_organisation_name))
async def correct_organization_name(query: CallbackQuery, state: FSMContext):
    await state.set_state(FSMAdvert.organization_erid)
    await query.message.bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                                      message_id=query.message.message_id, reply_markup=None)
    await query.message.edit_text(text='Отправьте пожалуйста erid токен вашей организации:')
    await query.answer()


@advert_fsm_router.message(StateFilter(FSMAdvert.organization_erid))
async def receive_organization_name(message: Message, state: FSMContext):
    organization_erid = message.text
    await state.update_data(organization_erid=organization_erid)
    await state.set_state(FSMAdvert.check_data)
    user_data = await state.get_data()
    markirovka_text = (f'Название организации: {user_data["organization_name"]}\nИНН организации: '
                       f'{user_data["organization_inn"]}\nERID организации: {user_data["organization_erid"]}\n')
    media_type = user_data['media_type']
    text = user_data['text'] + '\n\n\n\n' + markirovka_text
    await state.update_data(text=text)
    media_caption = text + '\n\n\n⬆️Вот так будет выглядеть ваше обявление!⬆️'
    if media_type == 'photo':
        await message.bot.send_photo(chat_id=message.chat.id, photo=user_data['media_id'], caption=media_caption,
                                     reply_markup=await confirm_data())
    else:
        await message.bot.send_video(chat_id=message.chat.id, video=user_data['media_id'], caption=media_caption,
                                     reply_markup=await confirm_data())


@advert_fsm_router.callback_query(F.data == 'create_advert_again', StateFilter(FSMAdvert.check_data))
async def create_advert_again(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await state.set_state(FSMAdvert.send_media)
    await query.message.answer(
        text=f'ШАГ 1. отправьте ТОЛЬКО ОДНО фото/видео в сжатом виде а не как файл',
        reply_markup=None)
    await query.answer()


@advert_fsm_router.callback_query(F.data == 'create_advert', StateFilter(FSMAdvert.check_data))
async def confirmed_data(query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    await query.answer(text='Создаем ваш заказ...', show_alert=True)
    await query.message.delete()
    res = await create_advert(user_data)
    if res == 'success':
        await query.message.answer(text='Заказ успешно создан✅Отправлено на модерацию💻')
        await bot_notify_moderators(text='Новый заказ на размещение объявления!💸')
    else:
        await query.message.answer(text=f'Заказ не был создан.❌\nРазработчики уже исправляют ошибку!💻')

    await state.update_data({})
    await state.clear()
    await query.answer()
    await cmd_start(message=query.message, state=None)
