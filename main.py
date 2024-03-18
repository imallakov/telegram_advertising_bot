from aiogram import Dispatcher
from aiogram.methods import DeleteWebhook
from aiogram.types import BotCommand, BotCommandScopeDefault
from bot import bot
import asyncio
import logging
from config_reader import config  # Импорт модуля для чтения конфигурации
from core.fsm.balance import balance_fsm_router
from core.fsm.question import question_fsm_router  # Импорт FSM-роутера для вопросов
from core.handlers.basic import basic_router  # Импорт базовых обработчиков
from core.handlers.client import client_router  # Импорт обработчиков клиентов
from core.handlers.admin import admin_router  # Импорт обработчиков администраторов
from core.fsm.advert import storage, advert_fsm_router  # Импорт хранилища и FSM-роутера для объявлений
from core.fsm.admin import admin_fsm_router  # Импорт FSM-роутера для администраторов
from core.handlers.moderator import moderator_router  # Импорт обработчиков модераторов
from core.handlers import apshed  # Импорт обработчиков для планировщика задач
from core.handlers.payment import payment_router  # Импорт обработчиков платежей

# Для записей с типом Secret* необходимо вызывать метод get_secret_value(),
# чтобы получить настоящее содержимое вместо '*******'

admin_id = int(config.admin_id.get_secret_value())  # Получение ID администратора из конфигурации

dp = Dispatcher(storage=storage)  # Создание диспетчера с указанием хранилища

dp.include_router(basic_router)  # Включение базовых обработчиков в диспетчер
dp.include_router(client_router)  # Включение обработчиков клиентов в диспетчер
dp.include_router(advert_fsm_router)  # Включение FSM-роутера для объявлений в диспетчер
dp.include_router(admin_router)  # Включение обработчиков администраторов в диспетчер
dp.include_router(admin_fsm_router)  # Включение FSM-роутера для администраторов в диспетчер
dp.include_router(moderator_router)  # Включение обработчиков модераторов в диспетчер
dp.include_router(question_fsm_router)  # Включение FSM-роутера для вопросов в диспетчер
dp.include_router(payment_router)  # Включение обработчиков платежей в диспетчер
dp.include_router(balance_fsm_router)


async def main():
    logging.basicConfig(level=logging.INFO)  # Настройка уровня логирования на INFO

    if type(apshed.scheduler.get_job(job_id='delete_adverts')) is None:
        apshed.scheduler.add_job(apshed.delete_adverts_from_channels, 'cron', hour=5, minute=59, second=0,
                                 id='delete_adverts')  # Планирование задачи удаления объявлений

    if type(apshed.scheduler.get_job(job_id='post_adverts')) is None:
        apshed.scheduler.add_job(apshed.publish_adverts_on_channels, 'cron', hour=6, minute=0, second=0,
                                 id='post_adverts')  # Планирование задачи публикации объявлений

    apshed.scheduler.start()  # Запуск планировщика задач

    try:
        await bot.set_my_commands([BotCommand(command='start', description='(пере)запустить бота')],
                                  BotCommandScopeDefault())  # Установка команды бота "start"
        await bot(DeleteWebhook(drop_pending_updates=True))  # Удаление вебхука бота с отложенными обновлениями
        await dp.start_polling(bot)  # Запуск опроса бота через диспетчер
    finally:
        await bot.session.close()  # Закрытие сессии бота


if __name__ == "__main__":
    asyncio.run(main())  # Запуск основной функции asyncio при запуске скрипта
