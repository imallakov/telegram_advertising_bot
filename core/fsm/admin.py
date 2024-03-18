from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot import can_post_in_chat, get_chat_by_username_from_telegram, bot_delete_message_from_chat
from core.database.requests import add_chat, add_tariffs, change_moderator_status
from core.keyboards.inline_keyboards import after_adding_new_tariff_keyboard, after_adding_new_chat_keyboard, \
    after_adding_new_moderator_keyboard

admin_fsm_router = Router()


class FSMAdmin(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодействия с пользователем
    add_chat = State()
    fsm_tariff = State()
    add_moderator = State()


@admin_fsm_router.message(StateFilter(FSMAdmin.add_moderator))
async def fsm_add_moderator(message: Message, state: FSMContext):
    user_id = None
    username = None
    if message.text.isdigit():
        user_id = int(message.text)
    else:
        username = message.text
        if username.startswith('@'):
            username = username[1:]
    res = await change_moderator_status(user_id=user_id, username=username, is_moderator=True)
    if res == 'success':
        answer = (f'Пользователь успешно добавлен в список модераторов✅')
    elif res == 'not_found':
        answer = (f'🤷🏻‍♂️Пользователь не найден в нашей базе данных. Пожалуйста, попросите сначала пользователя '
                  f'запустить наш бот. Потом заново попытайтесь добавить его в список модераторов'
                  f'Если вы отправили username пользователя, то попытайтесь отправить нам его USER ID при добавлении '
                  f'его в список модераторов🤔')
    else:
        answer = (f'Пользователь не добавлен в список модераторов❌\n'
                  f' Ошибка уже отправлена разработчикам🧑🏻‍💻')
    data = await state.get_data()
    message_id = data['message_id']
    await bot_delete_message_from_chat(chat_id=message.chat.id, message_id=message_id)
    await message.delete()
    await state.update_data({})
    await state.clear()
    await message.answer(
        text=answer,
        reply_markup=await after_adding_new_moderator_keyboard()
    )


@admin_fsm_router.message(StateFilter(FSMAdmin.add_chat))
async def get_chat_name(message: Message, state: FSMContext):
    chat_username: str = message.text
    if not chat_username.startswith('@'):
        chat_username = '@' + chat_username
    search_message = await message.answer(text=f'Searching for chat/channel with username: {chat_username}')
    can_post: str = await can_post_in_chat(chat_username)
    if can_post == 'success':
        chat = await get_chat_by_username_from_telegram(chat_username)
        if type(chat) is not str:
            res = await add_chat(chat_id=chat.id, chat_title=chat.title, chat_username=chat.username,
                                 chat_type=chat.type)
            if res == 'success':
                answer = f'Чат/канал @{chat.username} успешно добавлен✅'
            elif res == 'reactivated':
                answer = f'Чат/канал @{chat.username} успешно добавлен обратно в список выбора✅'
            elif res == 'exists':
                answer = f'Чат/канал @{chat.username} уже существует в базе✅'
            else:
                answer = (f'❗Ошибка❗\nЧат/канал @{chat.username} не добавлен❌\n'
                          f'Разработчики уже работают над решением проблемы🧑🏻‍💻')
        else:
            answer = f'Чат/канал {chat_username} не  существует🤷🏻‍♂️'
    else:
        answer = (f'Чат/канал {chat_username} не добавлен в список выборов. Нету разрешения на '
                  f'отправку поcта на канале/в чате ❌')
    data = await state.get_data()
    message_id = data['message_id']
    await bot_delete_message_from_chat(chat_id=message.chat.id, message_id=message_id)
    await message.delete()
    await search_message.delete()
    await state.update_data({})
    await state.clear()
    await message.answer(
        text=answer,
        reply_markup=await after_adding_new_chat_keyboard()
    )


@admin_fsm_router.message(StateFilter(FSMAdmin.fsm_tariff))
async def get_fsm_tariff(message: Message, state: FSMContext):
    temp = message.text.strip().split(',')
    tariffs: list[dict[str, int]] = []
    for unit in temp:
        day, price = unit.split('-')
        one_tariff: dict[str, int] = {'days': day, 'price': price}
        tariffs.append(one_tariff)
    data = await state.get_data()
    chat_id = data['chosen_chat_id']
    res = await add_tariffs(chat_id, tariffs)
    if res == 'success':
        answer = (f'Тарифы были успешно добавлены в список выборов✅')
    else:
        answer = f'Тарифы не были добавлены в список выборов❌ Ошибка уже отправлена разработчикам!'
    message_id = data['message_id']
    chat_username = data['chat_username']
    await bot_delete_message_from_chat(chat_id=message.chat.id, message_id=message_id)
    await message.delete()
    await state.update_data({})
    await state.clear()
    await message.answer(text=answer,
                         reply_markup=await after_adding_new_tariff_keyboard(chat_id=chat_id,
                                                                             chat_username=chat_username))
