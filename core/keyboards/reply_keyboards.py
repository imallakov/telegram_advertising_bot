from aiogram import types


async def main_menu(is_admin: bool, is_moderator: bool) -> types.ReplyKeyboardMarkup:
    kb = [
        [types.KeyboardButton(text="Личный кабинет"),
         types.KeyboardButton(text="Тех.поддержка")],
        [types.KeyboardButton(text="Разместить рекламу"),
         types.KeyboardButton(text="Пополнить баланс")],
    ]
    if is_admin and is_moderator:
        kb.append([types.KeyboardButton(text="Админка"),
                   types.KeyboardButton(text='Модерация')])
    elif is_admin:
        kb.append([types.KeyboardButton(text="Админка")])
    elif is_moderator:
        kb.append([types.KeyboardButton(text='Модерация')])
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите дальнейшее действие",
        one_time_keyboard=True,
    )
    return keyboard


async def cancel() -> types.ReplyKeyboardMarkup:
    kb = [
        [types.KeyboardButton(text="Отмена")]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Для отмены воспользуйтесь кнопкой отмены",
    )
    return keyboard


async def adminka() -> types.ReplyKeyboardMarkup:
    kb = [
        [types.KeyboardButton(text="добавить чат/канал"),
         types.KeyboardButton(text="добавить модератора")],
        [types.KeyboardButton(text="удалить чат/канал"),
         types.KeyboardButton(text="удалить модератора")],
        [types.KeyboardButton(text="Главное меню")],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите дальнейшее действие",
        one_time_keyboard=True
    )
    return keyboard
