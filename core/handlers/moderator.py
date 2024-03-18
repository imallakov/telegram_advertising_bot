from types import NoneType

from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from core.database.requests import get_moderator_info, get_moderating_adverts, get_advert_info, approve_advert, \
    decline_advert, get_moderating_question, get_all_undeleted_adverts, change_undeleted_status_to_done
from core.fsm.advert import FSMAdvert
from core.fsm.question import FSMQuestion
from core.handlers.basic import cmd_start
from core.keyboards.callbackdata import ModeratorDecision
from core.keyboards.inline_keyboards import moderator_menu, moderate_advert_keyboard, advert_info_keyboard, \
    deleting_undeleted_adverts
from core.keyboards.reply_keyboards import cancel

moderator_router = Router()


@moderator_router.callback_query(F.data == 'to_new_questions')
async def answer_to_question(query: CallbackQuery, state: FSMContext):
    question = await get_moderating_question()
    if type(question) is not NoneType:
        await query.answer()
        sent_message = await query.message.answer(text='Вопрос: \n'
                                                       f'{question.question}\n\nНапишите ответ на вопрос:',
                                                  reply_markup=await cancel())
        await state.set_state(FSMQuestion.answer_question)
        await state.update_data(question_id=question.id, message_id=query.message.message_id,
                                sent_message_id=sent_message.message_id)
    else:
        await query.answer('Не отвеченных вопросов больше нет!✅')
        await query.message.delete()
        await cmd_moderator(query.message)


@moderator_router.callback_query(ModeratorDecision.filter(F.decision == 'approve'))
async def show_advert_info(query: CallbackQuery, callback_data: ModeratorDecision):
    result = await approve_advert(query.message, callback_data.advert_id)
    if result == 'error':
        await query.answer(text='Произошла ошибка!⛔Уже исправляем ошибку!)', show_alert=True)
    await moderating_new_orders(query)


@moderator_router.callback_query(ModeratorDecision.filter(F.decision == 'decline'))
@moderator_router.callback_query(ModeratorDecision.filter(F.decision == 'surely_decline'))
async def show_advert_info(query: CallbackQuery, callback_data: ModeratorDecision, state: FSMContext):
    if callback_data.decision == 'decline':
        sent_message = await query.message.answer(text='Напишите пожалуйста причину отказа:')
        await state.set_state(FSMAdvert.decline_note)
        await state.update_data(advert_id=callback_data.advert_id, query_message_id=query.message.message_id,
                                query_id=query.id, sent_message_id=sent_message.message_id)
        await query.answer()
    else:
        user_data = await state.get_data()
        note = user_data['note']
        result = await decline_advert(advert_id=callback_data.advert_id, note=note)
        if result == 'error':
            await query.answer(text='Произошла ошибка!⛔Уже исправляем ошибку!)', show_alert=True)
        await state.update_data({})
        await state.clear()
        await moderating_new_orders(query)


@moderator_router.callback_query(F.data == 'delete_this_message')
async def delete_this_message(query: CallbackQuery):
    await query.answer()
    await query.message.delete()


@moderator_router.callback_query(ModeratorDecision.filter(F.decision == 'info'))
async def show_advert_info(query: CallbackQuery, callback_data: ModeratorDecision):
    text: str = await get_advert_info(advert_id=callback_data.advert_id)
    await query.message.answer(text=text, reply_markup=await advert_info_keyboard())
    await query.answer()


@moderator_router.callback_query(F.data == 'to_main_menu')
async def cmd_main_menu(query: CallbackQuery):
    await query.answer()
    await query.message.delete()
    await cmd_start(query.message, None)


@moderator_router.callback_query(F.data == 'to_new_orders')
async def moderating_new_orders(query: CallbackQuery):
    advert = await get_moderating_adverts()
    await query.answer()
    await query.message.delete()
    if type(advert) is not NoneType:
        media_type = advert.media_type
        if media_type == 'photo':
            await query.message.bot.send_photo(chat_id=query.message.chat.id, photo=advert.media_id,
                                               caption=advert.text,
                                               reply_markup=await moderate_advert_keyboard(advert.id))
        else:
            await query.message.bot.send_video(chat_id=query.message.chat.id, video=advert.media_id,
                                               caption=advert.text,
                                               reply_markup=await moderate_advert_keyboard(advert.id))
    else:
        await query.answer('Все заявки рассмотрены✅')
        await cmd_moderator(message=query.message)


@moderator_router.callback_query(F.data == 'to_undeleted_adverts')
async def moderating_new_orders(query: CallbackQuery):
    adverts = await get_all_undeleted_adverts()
    await query.answer()
    links: str = ""
    for advert in adverts:
        links = links + f't.me/{advert.chat_id}/{advert.posted_message_id}\n'
    await query.message.edit_text(text=links, reply_markup=await deleting_undeleted_adverts())
    await cmd_moderator(message=query.message)


@moderator_router.callback_query(F.data == 'after_deleting_undeleted_adverts')
async def after_deleting_undeleted_adverts_function(query: CallbackQuery):
    await change_undeleted_status_to_done()
    await query.message.delete()
    await query.answer()
    await cmd_moderator(message=query.message)


@moderator_router.callback_query(F.data == 'to_moderator_cabinet')
async def back_to_cmd_moderator(query: CallbackQuery):
    await query.message.delete()
    await query.answer()
    await cmd_moderator(message=query.message)


@moderator_router.message(F.text.lower() == "модерация")
async def cmd_moderator(message: types.Message):
    orders, questions, undeleted_adverts = await get_moderator_info()
    await message.answer(f'РЕЖИМ МОДЕРАЦИИ!\n'
                         f'Количество новых заявок: {orders}\n'
                         f'Количество новых вопросов: {questions}\n'
                         f'Количество не удаленных объявлений: {undeleted_adverts}',
                         reply_markup=await moderator_menu(orders, questions, undeleted_adverts))
