from types import NoneType

from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot import bot_send_error_message
from core.database.requests import create_user, get_user
from core.keyboards.reply_keyboards import main_menu

from config_reader import config

basic_router = Router()


@basic_router.message(Command("start"))
@basic_router.message(F.text.lower() == "главное меню")
async def cmd_start(message: types.Message, state: FSMContext | None):
    if state is not None:
        if not await state.get_state() is None:
            await state.update_data({})
            await state.clear()
    is_admin_config: bool = message.chat.id == int(config.admin_id.get_secret_value())
    if message.text == '/start':
        user = await create_user(user_id=message.from_user.id, username=message.from_user.username,
                                 full_name=message.from_user.full_name,
                                 is_admin=is_admin_config)
    else:
        user = await get_user(user_id=message.chat.id)
    if type(user) is not NoneType:
        sent_message = await message.answer("Выберите дальнейшее действие",
                                            reply_markup=await main_menu(is_admin=user.is_admin,
                                                                         is_moderator=user.is_moderator))
    else:
        await bot_send_error_message(text='Can\'t create a new user in database when \\start command was sent!')
        sent_message = await message.answer(
            "Произошла ошибка!❌\nРазработчики уже исправляют ошибку.\nПриносим извинения!")
