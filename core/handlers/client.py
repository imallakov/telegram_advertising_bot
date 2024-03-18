from types import NoneType

from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery

from core.database.requests import get_user, get_client_orders, delete_advert, get_advert
from core.fsm.advert import FSMAdvert
from core.handlers.basic import cmd_start
from core.keyboards.callbackdata import ClientCabinet
from core.keyboards.inline_keyboards import chats_choice, client_cabinet, my_orders_keyboard, are_you_sure_delete, \
    after_client_deletes_advert
from core.keyboards.reply_keyboards import cancel

client_router = Router()


@client_router.callback_query(ClientCabinet.filter(F.event == 'info'))
async def my_orders(query: CallbackQuery, callback_data: ClientCabinet):
    status = callback_data.status
    advert_id = callback_data.index
    advert = await get_advert(advert_id=advert_id)
    note = advert.note
    status_text = ''
    if status == 'approved':
        status_text = 'Одобрено✅\nОплатите объявление пока не истёк срок оплаты!'
    elif status == 'declined':
        status_text = f'Отказ❌\nПричина отказа:\n{note}'
    elif status == 'paid':
        status_text = 'Оплачено✅\nОбъявление будет опубликовано выбранный вами день!'
    elif status == 'published':
        status_text = 'Опубликовано🎉'
    else:
        status_text = 'На модерации🧑🏻‍💻\nКак только объявление будет рассмотрено мы отправим вам уведомление!'
    await query.answer(
        text=f'Чат/канал: {advert.chat.name if advert.chat is not None else "нет данных"}\n'
             f'Дата: {advert.posted_at.strftime("%d/%m/%Y")}\n'
             f'Срок: {advert.tariff.days if advert.tariff is not None else "х"} дней\n'
             f'Цена: {advert.tariff.price if advert.tariff is not None else "х"} ₽\n'
             f'Статус: {status_text}\n', show_alert=True)


@client_router.callback_query(ClientCabinet.filter(F.event == 'to_main_menu'))
async def to_main_menu_function(query: CallbackQuery, callback_data: ClientCabinet):
    await query.message.delete()
    await cmd_start(message=query.message, state=None)


@client_router.callback_query(ClientCabinet.filter(F.event == 'delete_order'))
async def delete_my_order(query: CallbackQuery, callback_data: ClientCabinet):
    status = callback_data.status
    if not (status == 'approved' or status == 'declined'):
        await query.answer(
            text='Объявление можно будет удалять после модерации(вне зависимости результата модерации) и ДО оплаты',
            show_alert=True)
    else:
        await query.message.delete()
        await query.message.answer(text='Вы уверены что хотите удалить объявление?',
                                   reply_markup=await are_you_sure_delete(current_index=int(callback_data.note),
                                                                          advert_id=callback_data.index))


@client_router.callback_query(ClientCabinet.filter(F.event == 'surely_delete_advert'))
async def surely_delete_my_order(query: CallbackQuery, callback_data: ClientCabinet):
    advert_id = int(callback_data.note)
    result = await delete_advert(advert_id=advert_id)
    if result == 'deleted':
        await query.message.edit_text(text='Объявление успешно удалено🗑️✅',
                                      reply_markup=await after_client_deletes_advert(index=callback_data.index))
    elif result == 'not_found':
        await query.message.edit_text(
            text='Произошла ошибка! Объявление не найдено в базе данных, очень странно🤔, попробуйте заново, '
                 'если ошибка не исчезнет напишите в тех.поддержку!',
            reply_markup=await after_client_deletes_advert(index=callback_data.index))
    else:
        await query.message.edit_text(text='❗Произошла ошибка❗Разработчики уже проинформированы🧑🏻‍💻',
                                      reply_markup=await after_client_deletes_advert(index=callback_data.index))


@client_router.callback_query(ClientCabinet.filter(F.event == 'to_client_cabinet'))
async def my_orders(query: CallbackQuery, callback_data: ClientCabinet):
    await query.message.delete()
    await cmd_cabinet(message=query.message)


@client_router.callback_query(ClientCabinet.filter(F.event == 'to_my_orders'))
async def my_orders(query: CallbackQuery, callback_data: ClientCabinet):
    my_orders = await get_client_orders(user_id=query.message.chat.id)
    if len(my_orders) > 0:
        advert = my_orders[min(callback_data.index, len(my_orders) - 1)]
        await query.message.delete()
        media_type = advert.media_type
        if media_type == 'photo':
            await query.message.bot.send_photo(chat_id=query.message.chat.id, photo=advert.media_id,
                                               caption=advert.text,
                                               reply_markup=await my_orders_keyboard(current_index=callback_data.index,
                                                                                     length=len(my_orders),
                                                                                     advert_id=advert.id,
                                                                                     advert_status=advert.status,
                                                                                     note=''))
        else:
            await query.message.bot.send_video(chat_id=query.message.chat.id, video=advert.media_id,
                                               caption=advert.text,
                                               reply_markup=await my_orders_keyboard(current_index=callback_data.index,
                                                                                     length=len(my_orders),
                                                                                     advert_id=advert.id,
                                                                                     advert_status=advert.status,
                                                                                     note=''))
    else:
        if callback_data.note == 'after_delete_order':
            await query.message.delete()
            await cmd_cabinet(message=query.message)
        else:
            await query.answer(text='У вас еще нет заявок на размещение рекламы🥺', show_alert=True)


@client_router.message(F.text.lower() == "личный кабинет")
async def cmd_cabinet(message: types.Message):
    if type(message.text) is str and not (type(message.text) is NoneType):
        if message.text.lower() == 'личный кабинет':
            await message.delete()
    user_id = message.chat.id
    user = await get_user(user_id)
    text = (f'Добро пожаловать в личный кабинет, {message.from_user.full_name}!\n'
            f'У вас {len(user.adverts) if type(user) is not NoneType else 0} заявок на размешение рекламы\n'
            # f'У вас {len(user.questions) if type(user) is not NoneType else 0} заданных вопросов\n'
            f'Ваш баланс: {user.balance if type(user) is not NoneType else 0}')
    if type(user) is not NoneType:
        if user.is_admin:
            text += f'\nВы являетесь админом этого бота!'
        elif user.is_moderator:
            text += f'\nВы являетесь модератором этого бота!'
    await message.answer(text, reply_markup=await client_cabinet())


@client_router.message(F.text.lower() == "разместить рекламу", StateFilter(default_state))
async def cmd_advert(message: types.Message, state: FSMContext):
    await message.answer(
        'Вы начали процесс размещения рекламы\n\nПожалуйста следуйте инструкциям\nДля отмены воспользуйтесь '
        'кнопкой "Отмена"',
        reply_markup=await cancel())
    sent_message = await message.answer(text='Пожалуйста, выберите чат/канал для размещение рекламы:',
                                        reply_markup=await chats_choice())
    # Устанавливаем состояние ожидания ввода имени
    await state.set_state(FSMAdvert.choose_chat)
    await state.update_data({'message_id': sent_message.message_id})
