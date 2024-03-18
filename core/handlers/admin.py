from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from core.database.requests import delete_tariff, delete_chat, change_moderator_status
from core.fsm.admin import FSMAdmin
from core.handlers.basic import cmd_start
from core.keyboards.callbackdata import AdminCabinet
from core.keyboards.inline_keyboards import admin_cabinet_main, admin_list_of_chats, inline_cancel_button, \
    admin_tariffs_of_chat, are_you_sure_deleting_chat, admin_list_of_moderators, are_you_sure_deleting_moderator

admin_router = Router()


@admin_router.callback_query(AdminCabinet.filter(F.event == 'to_admin_cabinet'))
@admin_router.message(F.text.lower() == "админка")
async def cmd_adminka(message: types.Message | CallbackQuery):
    if type(message) is types.Message:
        if message.text == 'админка':
            await message.delete()
        await message.answer('С возвращение Босс!', reply_markup=await admin_cabinet_main())
    else:
        await message.message.edit_text('С возвращение Босс!', reply_markup=await admin_cabinet_main())


@admin_router.callback_query(AdminCabinet.filter(F.event == 'to_chats'))
async def show_all_chats(query: CallbackQuery, callback_data: AdminCabinet, state: FSMContext):
    if await state.get_state() is not None:
        await state.update_data({})
        await state.clear()
    await query.message.edit_text('Чаты и каналы:', reply_markup=await admin_list_of_chats())
    await query.answer()


@admin_router.callback_query(AdminCabinet.filter(F.event == 'to_chat_with_id'))
async def show_all_chats(query: CallbackQuery, callback_data: AdminCabinet, state: FSMContext):
    if await state.get_state() is not None:
        await state.update_data({})
        await state.clear()
    await query.message.edit_text(f'Тарифы канала/чата @{callback_data.note}',
                                  reply_markup=await admin_tariffs_of_chat(chat_id=callback_data.index,
                                                                           chat_username=callback_data.note))
    await query.answer()


@admin_router.callback_query(AdminCabinet.filter(F.event == 'delete_tariff'))
async def show_all_chats(query: CallbackQuery, callback_data: AdminCabinet):
    result = await delete_tariff(tariff_id=callback_data.index)
    if result == 'deleted':
        await query.answer(text='Тарифф удален🗑️', show_alert=True)
    else:
        await query.answer(text='❗Ошибка❗\nТарифф не удалён. Ошибка уже отправлена разработчикам!', show_alert=True)
    await query.message.edit_text(text=query.message.text,
                                  reply_markup=await admin_tariffs_of_chat(chat_id=int(callback_data.note),
                                                                           chat_username=''))


@admin_router.callback_query(AdminCabinet.filter(F.event == 'add_new_tariff'))
async def add_new_tariff_func(query: CallbackQuery, callback_data: AdminCabinet, state: FSMContext):
    new_callback_data = AdminCabinet(event='to_chat_with_id', index=callback_data.index, note=callback_data.note).pack()
    await query.message.edit_text(text='Напишите количество дней и цену тариффа в таком виде:\n'
                                       'количествно_дней-цена\n'
                                       'Если хотите много тариффов одновременно разделяйте их пробелами, '
                                       'не ставьте пробелов! Пример:\n'
                                       '1-100,2-300,4-800', reply_markup=await inline_cancel_button(new_callback_data))
    await state.set_state(FSMAdmin.fsm_tariff)
    await state.update_data(chosen_chat_id=callback_data.index, message_id=query.message.message_id,
                            chat_username=callback_data.note)


@admin_router.callback_query(AdminCabinet.filter(F.event == 'add_new_chat'))
async def show_all_chats(query: CallbackQuery, callback_data: AdminCabinet, state: FSMContext):
    new_callback_data = AdminCabinet(event='to_chats', index=0, note='').pack()
    await query.message.edit_text(
        text='Пожалуйста, отправьте username чата/канала. Если хотите отменить действие нажмите кнопку Отмена внизу',
        reply_markup=await inline_cancel_button(new_callback_data))
    await state.set_state(FSMAdmin.add_chat)
    await state.update_data(message_id=query.message.message_id)


@admin_router.callback_query(AdminCabinet.filter(F.event == 'delete_chat'))
async def show_all_chats(query: CallbackQuery, callback_data: AdminCabinet):
    await query.message.edit_text(text=f'Вы уверены что хотите удалит канал/чат @{callback_data.note} ?',
                                  reply_markup=await are_you_sure_deleting_chat(chat_id=callback_data.index,
                                                                                chat_username=callback_data.note))


@admin_router.callback_query(AdminCabinet.filter(F.event == 'surely_delete_chat'))
async def show_all_chats(query: CallbackQuery, callback_data: AdminCabinet):
    chat_id = callback_data.index
    res = await delete_chat(chat_id=chat_id)
    if res == 'deactivated':
        answer = f'Канал/чат успешно удалён из списка выбора🗑️'
    elif res == 'not_found':
        answer = (f'Канал/чат не был найден в базе🤷🏻‍♂️\nОчень странно ... 🤔\n'
                  f'Напишите тех.поддержке и сообщите разработчикам об случившимся💬')
    else:
        answer = f'Канал/чат не удалён❌\nРазработчики уже проинформированы🧑🏻‍💻'
    await query.answer(text=answer, show_alert=True)
    await query.message.edit_text(text=query.message.text, reply_markup=await admin_list_of_chats())


@admin_router.callback_query(AdminCabinet.filter(F.event == 'to_moderators'))
async def show_all_chats(query: CallbackQuery, callback_data: AdminCabinet, state: FSMContext):
    if await state.get_state() is not None:
        await state.update_data({})
        await state.clear()
    await query.message.edit_text(text='Список модераторов:', reply_markup=await admin_list_of_moderators())


@admin_router.callback_query(AdminCabinet.filter(F.event == 'add_new_moderator'))
async def add_new_moderator(query: CallbackQuery, callback_data: AdminCabinet, state: FSMContext):
    new_callback_data = AdminCabinet(event='to_moderators', index=0, note='').pack()
    await query.message.edit_text(
        text='Пожалуйста, сначала попросите модератора запустить у себя наш чтоб мы добавили его '
             'аккаунт в базу данных или же обновили данные об его аккаунте.\n'
             'А потом отправьте пожалуйста `UserID` или `username`(если есть) пользователя\n'
             'Если хотите отменить действие нажмите кнопку Отмена внизу',
        reply_markup=await inline_cancel_button(new_callback_data))
    await state.set_state(FSMAdmin.add_moderator)
    await state.update_data(message_id=query.message.message_id)


@admin_router.callback_query(AdminCabinet.filter(F.event == 'delete_moderator'))
async def show_all_chats(query: CallbackQuery, callback_data: AdminCabinet):
    await query.message.edit_text(
        text=f'Вы уверены что хотите удалит модератора @{callback_data.note} (User ID: {callback_data.index}) ?',
        reply_markup=await are_you_sure_deleting_moderator(user_id=callback_data.index,
                                                           user_username=callback_data.note))


@admin_router.callback_query(AdminCabinet.filter(F.event == 'surely_delete_moderator'))
async def show_all_chats(query: CallbackQuery, callback_data: AdminCabinet):
    user_id = callback_data.index
    res = await change_moderator_status(user_id=user_id, username=None, is_moderator=False)
    if res == 'success':
        answer = f'Модератор успешно удалён🗑️'
    elif res == 'not_found':
        answer = (f'Модератор не был найден в базе🤷🏻‍♂️\nОчень странно ... 🤔\n'
                  f'Напишите тех.поддержке и сообщите разработчикам об случившимся💬')
    else:
        answer = f'Модератор не удалён❌\nРазработчики уже проинформированы🧑🏻‍💻'
    await query.answer(text=answer, show_alert=True)
    await query.message.edit_text(text='Список модераторов:', reply_markup=await admin_list_of_moderators())


@admin_router.callback_query(AdminCabinet.filter(F.event == 'to_main_menu'))
async def show_all_chats(query: CallbackQuery, callback_data: AdminCabinet):
    await query.answer(text='Перенаправляем вас на главное меню!')
    await query.message.delete()
    await cmd_start(message=query.message, state=None)


@admin_router.callback_query(F.data == 'nothing')
async def nothing_function(query: CallbackQuery):
    await query.answer()
