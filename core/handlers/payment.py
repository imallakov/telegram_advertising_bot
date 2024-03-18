from datetime import datetime, timedelta

from aiogram import Bot, Router, F
from aiogram.types import Message, LabeledPrice, pre_checkout_query, CallbackQuery

from bot import bot_send_error_message
from . import apshed
import pytz

from config_reader import config
from .basic import cmd_start
from ..database.requests import change_advert_info, add_to_user_balance_amount
from ..keyboards.inline_keyboards import advert_payment_keyboard

payment_token = config.payment_token.get_secret_value()

payment_router = Router()


async def send_balance_top_up_invoice(message: Message, amount: int):
    sent_invoice = await message.bot.send_invoice(
        chat_id=message.chat.id,
        title='Пополнение баланса',
        description=f'Сумма: {amount}',
        payload=f'balance_user_id:{message.chat.id}|{amount}',
        provider_token=payment_token,
        currency='RUB',
        prices=[
            LabeledPrice(
                label='Пополнение баланса',
                amount=100 * amount
            ),
        ],
        start_parameter='reklamxbot',
        provider_data=None,
        protect_content=True,
    )


async def send_advert_invoice(bot: Bot, channel_username, post_date, delete_date, advert_id, price, user_id):
    try:
        await bot.send_message(text=f'Ваша заявка на размещение рекламы на канала/чате @{channel_username} '
                                    f'была одобрено модератором✅\nУправлять своими заявками можете в личном '
                                    f'кабинете, а вопросы можете задать в тех.поддержку!\n\n'
                                    f'Оплатите заказ в течение 15мин! Иначе заявке будет отказано!', chat_id=user_id)
        sent_invoice = await bot.send_invoice(
            chat_id=user_id,
            title='Оплата размещения объявления',
            description=f'Размещение объявления\n'
                        f'Дата публикации: {post_date}\n'
                        f'Дата удаления: {delete_date}\n',
            payload=f'advert_id:{advert_id}',
            provider_token=payment_token,
            currency='RUB',
            prices=[
                LabeledPrice(
                    label='Размещение объявления',
                    amount=100 * price
                ),
            ],
            start_parameter='reklamxbot',
            provider_data=None,
            protect_content=True,
            reply_markup=await advert_payment_keyboard(user_id=user_id, advert_id=advert_id)
        )

        apshed.scheduler.add_job(apshed.delete_advert_invoice_after_deadline, trigger='date',
                                 run_date=datetime.now(pytz.timezone('Europe/Moscow')) + timedelta(minutes=15),
                                 id=f'delete_advert_invoice_{user_id}_{advert_id}',
                                 kwargs={'chat_id': sent_invoice.chat.id, 'message_id': sent_invoice.message_id,
                                         'advert_id': advert_id})
    except Exception as error:
        await bot_send_error_message(
            f'send_advert_invoice:\nError: {error.__str__()}')


@payment_router.callback_query(F.data.startswith('balance_pay'))
async def write_off_from_balance(query: CallbackQuery):
    _, details = query.data.split(':')
    user_id, advert_id = details.split('|')
    amount = (-1) * query.message.invoice.total_amount / 100
    res = await add_to_user_balance_amount(user_id=int(user_id), amount=int(amount))
    if res == 'success':
        await change_advert_info(advert_id=int(advert_id), posted_message_id=-1, status='paid', note='')
        await query.message.delete()
        await query.message.answer(text='Успешно списано с баланса✅')
    elif res == 'valueerror':
        await query.answer(text='Не хватает средств на балансе!❌', show_alert=True)
    else:
        await query.answer(text='Произошла ошибка, уже исправляем! Оплатите пока с карты', show_alert=True)
    await query.answer()


@payment_router.pre_checkout_query()
async def pre_checkout_query_answer(pcq: pre_checkout_query, bot: Bot):
    await bot.answer_pre_checkout_query(pcq.id, ok=True)


@payment_router.message(F.successful_payment)
async def successfull_payment(message: Message):
    type, info = message.successful_payment.invoice_payload.split(':')
    if type == 'advert_id':
        await change_advert_info(advert_id=int(info), posted_message_id=-1, status='paid', note='')
        msg = 'Объявление успешно оплачено!'
        apshed.scheduler.remove_job(job_id=f'delete_advert_invoice_{message.chat.id}_{info}')
        await message.answer(msg)
    elif type == 'balance_user_id':
        user_id, amount = info.split('|')
        ans = await add_to_user_balance_amount(user_id=int(user_id), amount=int(amount))
        if ans == 'error':
            msg_text = '❌Произошла ошибка! Разработчики уже работают над ним!'
        elif ans == 'not_found':
            msg_text = (f'Пользователь не найден в базе🤷🏻‍♂️\nОчень странно ... 🤔\n'
                        f'Напишите тех.поддержке и сообщите разработчикам об случившимся💬')
        else:
            msg_text = f'Баланс успешно пополнен!✅'
        await message.answer(text=msg_text)
    await cmd_start(message, None)
