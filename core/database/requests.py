import datetime
from types import NoneType
from typing import Any

from sqlalchemy import select, exc, func, asc, not_
from sqlalchemy.orm import selectinload

from bot import bot_send_message, bot_send_error_message
from .models import User, Chat, async_session, Tariff, Advert, Question


async def get_all_chats() -> list[Chat]:
    try:
        async with async_session() as session:
            chats = await session.execute(select(Chat))
            return chats.scalars().all()
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'get_all_chats:\nError: {error.__str__()}')
        return []


async def is_user_exists(user_id: int) -> bool:
    try:
        async with async_session() as session:
            sql_res = await session.execute(select(User).where(User.id == user_id))
            res = sql_res.scalars().first()
            if type(res) is not NoneType:
                return True
            else:
                return False
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'is_user_exists:\nuser_id={user_id}\nError: {error.__str__()}')
        return False


async def is_chat_exists(chat_id: int) -> bool:
    try:
        async with async_session() as session:
            sql_res = await session.execute(select(Chat).where(Chat.id == chat_id))
            res = sql_res.scalars().first()
            if type(res) is not NoneType:
                return True
            else:
                return False
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'is_chat_exists:\nchat_id={chat_id}\nError: {error.__str__()}')
        return False


async def delete_chat(chat_id: int) -> str:
    try:
        if await is_chat_exists(chat_id):
            async with async_session() as session:
                chat = await session.get(Chat, chat_id)
                if chat:
                    # await session.delete(chat)
                    chat.is_active = False
                    await session.commit()
                    return 'deactivated'
                else:
                    return 'not_found'
        else:
            return 'not_found'
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'delete_chat:\nchat_id={chat_id}\nError: {error.__str__()}')
        return 'error'


async def add_chat(chat_id: int, chat_title: str | None, chat_username: str | None, chat_type: str) -> str:
    try:
        if not await is_chat_exists(chat_id=chat_id):
            async with async_session() as session:
                if type(chat_title) is None:
                    chat_title: str = ''
                chat = Chat(id=chat_id, name=chat_title, username=chat_username, type=chat_type)
                session.add(chat)
                await session.commit()
            return 'success'
        else:
            async with async_session() as session:
                chat = await session.get(Chat, chat_id)
                if chat:
                    # await session.delete(chat)
                    if chat.is_active is False:
                        chat.is_active = True
                        await session.commit()
                        return 'reactivated'
                    else:
                        return 'exists'
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'add_chat:\nchat_id={chat_id}\nchat_title={chat_title}\nError: {error.__str__()}')
        return 'error'


async def add_tariffs(chat_id: int, tariffs: list[dict[str, int]]) -> str:
    try:
        async with async_session() as session:
            for unit in tariffs:
                tariff = Tariff(days=int(unit['days']), price=int(unit['price']), chat_id=chat_id)
                session.add(tariff)
            await session.commit()
        return 'success'
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'add_tariffs:\nchat_id={chat_id}\ntariffs:{tariffs}\nError: {error.__str__()}')
        return error.__str__()


async def delete_tariff(tariff_id: int) -> str:
    try:
        async with async_session() as session:
            chat = await session.get(Tariff, tariff_id)
            if chat:
                await session.delete(chat)
                await session.commit()
                return 'deleted'
            else:
                return 'not_found'
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'delete_tariff:\ntariff_id={tariff_id}\nError: {error.__str__()}')
        return 'error'


async def create_user(user_id: int, username: str | None, full_name: str, is_admin: bool = False,
                      is_moderator: bool = False,
                      balance: int = 0) -> User | None:
    try:
        if type(username) is None:
            username = ''
        if not await is_user_exists(user_id):
            async with async_session() as session:
                # if is_admin:
                #     is_moderator = True
                user = User(id=user_id, username=username, full_name=full_name, is_admin=is_admin,
                            is_moderator=is_moderator,
                            balance=balance)
                session.add(user)
                await session.commit()
                return await get_user(user_id)
        else:
            async with async_session() as session:
                result = await session.execute(
                    select(User)
                    .filter(User.id == user_id)  # type: ignore
                )
                user = result.scalars().first()
                user.username = username
                user.full_name = full_name
                await session.commit()
                return await get_user(user_id)
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'create_user:\nuser_id={user_id}\nusername={username}\nError: {error.__str__()}')
        return None


async def change_moderator_status(user_id: int | None = None, username: str | None = None,
                                  is_moderator: bool = False) -> str:
    try:
        async with async_session() as session:
            if type(user_id) is not NoneType:
                result = await session.execute(
                    select(User)
                    .filter(User.id == user_id)
                )
            else:
                result = await session.execute(
                    select(User)
                    .filter(User.username == username)
                )
            user = result.scalars().first()
            if type(user) is not NoneType:
                user.is_moderator = is_moderator
                await session.commit()
                return 'success'
            else:
                return 'not_found'
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'change_moderator_status:\nuser_id={user_id}\nusername={username}\nError: {error.__str__()}')
        return 'error'


async def add_to_user_balance_amount(user_id: int, amount: int) -> str:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User)
                .filter(User.id == user_id)
            )
            user = result.scalars().first()
            if type(user) is not NoneType:
                if user.balance + amount >= 0:
                    user.balance += amount
                    await session.commit()
                    return 'success'
                else:
                    return 'valueerror'
            else:
                return 'not_found'
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'add_to_user_balance_amount:\nuser_id={user_id}\nError: {error.__str__()}')
        return 'error'


async def get_user(user_id: int) -> User | None:
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User)
                .options(selectinload(User.adverts), selectinload(User.questions))
                .filter(User.id == user_id)  # type: ignore
            )
            return result.scalars().first()
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'get_user:\nuser_id={user_id}\nError: {error.__str__()}')
        return None


async def get_adverts_in_this_month(chat_id: int, month: int, year: int) -> list[int]:
    try:
        async with async_session() as session:
            query = select(
                func.array_agg(func.extract("day", Advert.posted_at)).label("posted_days")
            ).filter(
                Advert.chat_id == chat_id,  # Filter by chat ID
                func.extract("month", Advert.created_at) == month,  # Filter by month
                func.extract("year", Advert.created_at) == year,  # Filter by year
                not_(Advert.status == 'declined')
            )
            res = await session.execute(query)
            results = res.scalars().all()
            if type(results[0]) is NoneType:
                results[0]: list[int] = []
            advert_days: list[int] = results[0]
            return advert_days
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'get_adverts_in_this_month:\nchat_id={chat_id}\nmonth={month}\nyear={year}\nError: {error.__str__()}')
        return []


async def get_tariffs_of_chat(chat_id: int) -> list[Tariff]:
    try:
        async with async_session() as session:
            query = select(Tariff).options(selectinload(Tariff.chat)).filter_by(chat_id=chat_id).order_by(
                asc(Tariff.days))  # Filter tariffs by chat ID
            result = await session.execute(query)  # Fetch all tariffs as Tariff objects
            tariffs = result.scalars().all()
            return tariffs
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'get_tariffs_of_chat:\nchat_id={chat_id}\nError: {error.__str__()}')
        return []


async def get_moderators() -> list[User]:
    try:
        async with async_session() as session:
            query = select(User).filter_by(is_moderator=True)
            result = await session.execute(query)
            moderators = result.scalars().all()
            return moderators
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'get_moderators:\nError: {error.__str__()}')
        return []


async def create_advert(data: dict[str, Any]) -> str:
    try:
        async with async_session() as session:
            # if not await is_user_exists(data['user_id']):
            #     await create_user(user_id=data['user_id'], is_admin=False, is_moderator=False, balance=0)
            advert = Advert(
                user_id=data['user_id'],
                chat_id=data['chat_id'],
                tariff_id=data['tariff_id'],
                media_id=data['media_id'],
                media_type=data['media_type'],
                text=data['text'],
                posted_at=datetime.date(year=data['year'], month=data['month'], day=data['day']),
                deleted_at=datetime.date(year=data['year'], month=data['month'], day=data['day']) + datetime.timedelta(
                    data['days'])
            )
            session.add(advert)
            await session.commit()
            return 'success'
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'create_advert:\ndata={data}\nError: {error.__str__()}')
        return 'error'


async def delete_advert(advert_id: int) -> str:
    try:
        async with async_session() as session:
            advert = await session.get(Advert, advert_id)
            if advert:
                await session.delete(advert)
                await session.commit()
                return 'deleted'
            else:
                return 'not_found'
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'delete_advert:\nadvert_id={advert_id}\nError: {error.__str__()}')
        return 'error'


async def get_moderator_info() -> (int, int, int):
    try:
        async with async_session() as session:
            advert_query = select(func.count(Advert.id)).filter(Advert.status == 'moderating')
            question_query = select(func.count(Question.id)).filter(Question.status == 'open')
            undeleted_advert_query = select(func.count(Question.id)).filter(Question.status == 'undeleted')
            advert_res = await session.execute(advert_query)
            question_res = await session.execute(question_query)
            undeleted_advert_res = await session.execute(undeleted_advert_query)
            advert_count = advert_res.scalar()
            question_count = question_res.scalar()
            undeleted_advert_count = undeleted_advert_res.scalar()
            return advert_count, question_count, undeleted_advert_count
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'get_moderator_info:\nError: {error.__str__()}')
        return 0, 0


async def get_moderating_adverts() -> Advert | None:
    try:
        async with async_session() as session:
            query = select(Advert).filter_by(status="moderating").order_by(
                asc(Advert.posted_at))
            res = await session.execute(query)
            result = res.scalars().first()
            return result
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'get_moderating_adverts:\nError: {error.__str__()}')
        return None


async def get_all_undeleted_adverts():
    try:
        async with async_session() as session:
            query = select(Advert).filter_by(status="undeleted").order_by(
                asc(Advert.posted_at))
            res = await session.execute(query)
            result = res.scalars().all()
            return result
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'get_all_undeleted_adverts:\nError: {error.__str__()}')
        return None


async def change_undeleted_status_to_done():
    try:
        async with async_session() as session:
            query = select(Advert).filter_by(status="undeleted").order_by(
                asc(Advert.posted_at))
            res = await session.execute(query)
            result = res.scalars().all()
            for res in result:
                res.status = "done"
            session.commit()
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'change_undeleted_status_to_done:\nError: {error.__str__()}')


async def get_advert(advert_id) -> Advert | None:
    try:
        async with async_session() as session:
            query = select(Advert).options(selectinload(Advert.tariff), selectinload(Advert.chat),
                                           selectinload(Advert.user)).filter_by(id=advert_id)
            res = await session.execute(query)
            result = res.scalars().first()
            return result
    except Exception as error:
        await bot_send_error_message(
            f'get_advert:\nadvert_id={advert_id}\nError: {error.__str__()}')
        return None


async def get_advert_info(advert_id) -> str:
    try:
        async with async_session() as session:
            query = select(Advert).options(selectinload(Advert.tariff), selectinload(Advert.chat),
                                           selectinload(Advert.user)).filter_by(
                id=advert_id)
            res = await session.execute(query)
            result = res.scalar()
            username = result.user.username
            if len(username) > 0:
                username = '@' + username
            else:
                username = 'Не найдено'
            text = (f'Заказчик: USER ID = {result.user.id}\n'
                    f'Заказчик: USERNAME = {username}\n'
                    f'Чат/канал: {result.chat.name} (@{result.chat.username})\n'
                    f'Дата публикации: {result.posted_at.strftime("%d/%m/%Y")}\n'
                    f'Тарифф: {result.tariff.days}дней - {result.tariff.price}₽')
            return text
    except Exception as error:
        await bot_send_error_message(
            f'get_advert_info:\nadvert_id={advert_id}\nError: {error.__str__()}')
        return 'error'


async def approve_advert(message, advert_id) -> str:
    try:
        answer = ''
        async with async_session() as session:
            query = select(Advert).options(selectinload(Advert.chat), selectinload(Advert.user),
                                           selectinload(Advert.tariff)).filter_by(id=advert_id)
            res = await session.execute(query)
            result = res.scalars().first()
            if type(result) is not NoneType:
                result.status = 'approved'
                from ..handlers.payment import send_advert_invoice
                await send_advert_invoice(bot=message.bot, channel_username=result.chat.username,
                                          post_date=result.posted_at.strftime("%d/%m/%Y"),
                                          delete_date=result.deleted_at.strftime("%d/%m/%Y"), price=result.tariff.price,
                                          advert_id=result.id, user_id=result.user_id)
                await session.commit()
                answer = 'approved'
            else:
                answer = 'not_found'
        return answer
    except Exception as error:
        await bot_send_error_message(
            f'approve_advert:\nadvert_id={advert_id}\nError: {error.__str__()}')
        return 'error'


async def decline_advert(advert_id, note: str = '') -> str:
    try:
        async with async_session() as session:
            query = select(Advert).options(selectinload(Advert.chat)).filter_by(id=advert_id)
            res = await session.execute(query)
            result = res.scalars().first()
            if type(result) is not NoneType:
                result.status = 'declined'
                result.note = note
                await bot_send_message(to_chat=result.user_id,
                                       text=f'Ваша заявка на размещение рекламу на канала/чате {result.chat.name} '
                                            f'было отклонено модератором❌\n'
                                            f'Причина отказа:\n{note}\n\n'
                                            f'Свои заявки можете смотреть в личном '
                                            f'кабинете, а вопросы можете задать в тех.поддержку!')
                await session.commit()
                return 'declined'
            else:
                return 'not_found'
    except Exception as error:
        await bot_send_error_message(
            f'decline_advert:\nadvert_id={advert_id}\nnote={note}\nError: {error.__str__()}')
        return 'error'


async def get_adverts_to_delete() -> list[Advert]:
    try:
        async with async_session() as session:
            today = datetime.datetime.now().date()
            query = select(Advert).options(selectinload(Advert.chat)).filter(Advert.deleted_at >= today,
                                                                             Advert.deleted_at < today + datetime.timedelta(
                                                                                 days=1))
            res = await session.execute(query)
            result = res.scalars().all()
            return result
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(f'get_adverts_to_delete:\nError: {error.__str__()}')
        return []


async def get_adverts_to_publish() -> list[Advert]:
    try:
        async with async_session() as session:
            today = datetime.datetime.now().date()
            query = select(Advert).options(selectinload(Advert.chat)).filter(Advert.status == 'paid',
                                                                             Advert.posted_at >= today,
                                                                             Advert.posted_at < today + datetime.timedelta(
                                                                                 days=1))
            res = await session.execute(query)
            result = res.scalars().all()
            return result
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(f'get_adverts_to_publish:\nError: {error.__str__()}')
        return []


async def change_advert_info(advert_id: int, posted_message_id, status, note: str):
    try:
        async with async_session() as session:
            advert = await session.get(Advert, advert_id)
            if advert:
                # await session.delete(chat)
                if not posted_message_id == -1:
                    advert.posted_message_id = posted_message_id
                advert.status = status
                if len(note) > 0:
                    advert.note = note
                await session.commit()
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(f'change_advert_info:\nError: {error.__str__()}')


async def get_client_orders(user_id) -> list[Advert]:
    try:
        async with async_session() as session:
            query = select(Advert).filter_by(user_id=user_id).order_by(
                asc(Advert.created_at))
            res = await session.execute(query)
            result = res.scalars().all()
            return result
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'get_client_orders:\n user_id={user_id}\nError: {error.__str__()}')
        return []


async def create_question(user_id, question: str) -> str:
    try:
        async with async_session() as session:
            # if not await is_user_exists(user_id):
            #     await create_user(user_id=user_id, is_admin=False, is_moderator=False, balance=0)
            question = Question(
                user_id=user_id,
                question=question
            )
            session.add(question)
            await session.commit()
            return 'success'
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'create_question:\n user_id={user_id}\n question={question}\n Error: {error.__str__()}')
        return 'error'


async def get_moderating_question() -> Question | None:
    try:
        async with async_session() as session:
            query = select(Question).filter_by(status="open").order_by(
                asc(Question.created_at))
            res = await session.execute(query)
            result = res.scalars().first()
            return result
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'get_moderating_question: \nError: {error.__str__()}')
        return None


async def save_answer_to_question(question_id, answer) -> str:
    try:
        async with async_session() as session:
            query = select(Question).filter_by(id=question_id)
            res = await session.execute(query)
            result = res.scalars().first()
            result.answer = answer
            result.answered_at = datetime.date.today()
            result.status = 'closed'
            await bot_send_message(to_chat=result.user_id, text='❗❗❗Модератор ответил на ваш вопрос❗❗❗\n'
                                                                f'Ваш Вопрос:\n{result.question}\n\n'
                                                                f'Ответ модератора:\n{answer}\n')
            await session.commit()
            return 'success'
    except exc.SQLAlchemyError as error:
        await bot_send_error_message(
            f'save_answer_to_question: question_id={question_id} answer={answer} Error: {error.__str__()}')
        return 'error'
