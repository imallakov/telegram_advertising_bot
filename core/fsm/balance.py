from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message

from core.handlers.payment import send_balance_top_up_invoice

storage = RedisStorage.from_url("redis://172.20.147.45:6379/0")

balance_fsm_router = Router()


class FSMBalance(StatesGroup):
    enter_amount = State()


@balance_fsm_router.message(F.text.lower() == 'пополнить баланс', StateFilter(default_state))
async def top_up_balance_button(message: Message, state: FSMContext):
    await state.set_state(FSMBalance.enter_amount)
    await message.answer(text='Внесите сумму для пополнения баланса:')


@balance_fsm_router.message(StateFilter(FSMBalance.enter_amount))
async def entered_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
    except ValueError as error:
        await message.answer(text='Напишите сумму только цифрами')
    else:
        await state.update_data({})
        await state.clear()
        await send_balance_top_up_invoice(message=message, amount=amount)
