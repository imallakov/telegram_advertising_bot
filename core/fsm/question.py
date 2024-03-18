from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardRemove

from bot import bot_delete_message_from_chat
from core.database.requests import create_question, save_answer_to_question
from core.handlers.apshed import bot_notify_moderators
from core.handlers.basic import cmd_start
from core.keyboards.inline_keyboards import to_next_question
from core.keyboards.reply_keyboards import cancel

storage = MemoryStorage()

question_fsm_router = Router()


class FSMQuestion(StatesGroup):
    ask_question = State()
    answer_question = State()


@question_fsm_router.message(F.text.lower() == 'отмена', StateFilter(FSMQuestion.answer_question))
async def get_answer_to_question(message: Message, state: FSMContext):
    user_data = await state.get_data()
    question_id = user_data['question_id']
    qmessage_id = user_data['message_id']
    sent_message_id = user_data['sent_message_id']
    await bot_delete_message_from_chat(chat_id=message.chat.id, message_id=qmessage_id)
    await bot_delete_message_from_chat(chat_id=message.chat.id, message_id=sent_message_id)
    await state.update_data({})
    await state.clear()
    await message.answer(text='Вы отменили процесс ответа на вопросы... Перенаправляем вас на кабинет модератора',
                         reply_markup=ReplyKeyboardRemove())
    from core.handlers.moderator import cmd_moderator
    await cmd_moderator(message)


@question_fsm_router.message(StateFilter(FSMQuestion.answer_question))
async def get_answer_to_question(message: Message, state: FSMContext):
    user_data = await state.get_data()
    question_id = user_data['question_id']
    qmessage_id = user_data['message_id']
    sent_message_id = user_data['sent_message_id']
    result = await save_answer_to_question(question_id=question_id, answer=message.text)
    await bot_delete_message_from_chat(chat_id=message.chat.id, message_id=qmessage_id)
    await bot_delete_message_from_chat(chat_id=message.chat.id, message_id=sent_message_id)
    await state.update_data({})
    await state.clear()
    text = 'Ответ успешно сохранен! Для того чтоб перейти на след вопрос нажмите кнопку ниже!'
    if result == 'error':
        text = 'Произошла ошибка. Уже работаем над исправлением ошибки!'
    await message.answer(text=text, reply_markup=await to_next_question())


@question_fsm_router.message(F.text.lower() == 'тех.поддержка', StateFilter(default_state))
async def support_func(message: Message, state: FSMContext):
    await state.set_state(FSMQuestion.ask_question)
    await message.delete()
    sent_message = await message.answer(text='Напишите пожалуйста свой вопрос:', reply_markup=await cancel())
    await state.update_data(message_id=sent_message.message_id)


@question_fsm_router.message(F.text.lower() == "отмена", StateFilter(FSMQuestion.ask_question))
async def cancel_state(message: Message, state: FSMContext):
    user_data = await state.get_data()
    await bot_delete_message_from_chat(message.chat.id, user_data['message_id'])
    await message.delete()
    await state.clear()
    await state.update_data({})
    await cmd_start(message, None)


@question_fsm_router.message(StateFilter(FSMQuestion.ask_question))
async def send_question(message: Message, state: FSMContext):
    user_data = await state.get_data()
    await bot_delete_message_from_chat(chat_id=message.chat.id, message_id=user_data['message_id'])
    await message.delete()
    result = await create_question(user_id=message.chat.id, question=message.text)
    if result == 'success':
        await message.answer(
            text='✅Ваш вопрос был отправлен модераторам! Как только они ответят мы отправим вам уведомление!')
        await bot_notify_moderators(text='Новый вопрос от пользователя!💭')
    else:
        await message.answer(
            text='❌Произошла ошибка! Мы уже работаем над ней!🧑🏻‍💻')
    await cmd_start(message=message, state=None)
    await state.update_data({})
    await state.clear()
