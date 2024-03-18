from datetime import datetime, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot import bot_delete_message_from_chat, bot_post_advert, bot, bot_send_message
from core.database.requests import get_adverts_to_delete, get_adverts_to_publish, change_advert_info, get_moderators
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler_di import ContextSchedulerDecorator

jobstores = {
    'default': RedisJobStore(jobs_key='dispatched_trips_jobs', run_times_key='dispatched_trips_running',
                             host='localhost', db=2, port=6379)
}
scheduler = ContextSchedulerDecorator(AsyncIOScheduler(timezone='Europe/Moscow', jobstores=jobstores))


async def delete_adverts_from_channels():
    adverts = await get_adverts_to_delete()
    for advert in adverts:
        result = await bot_delete_message_from_chat(chat_id=advert.chat.id, message_id=advert.posted_message_id)
        if result == 'error':
            await change_advert_info(advert_id=advert.id, posted_message_id=-1, status='undeleted', note='')
        else:
            await change_advert_info(advert_id=advert.id, posted_message_id=-1, status='done', note='')


async def publish_adverts_on_channels():
    adverts = await get_adverts_to_publish()
    for advert in adverts:
        result = await bot_post_advert(media_id=advert.media_id, media_type=advert.media_type, chat_id=advert.chat.id,
                                       chat_type=advert.chat.type, text=advert.text)
        if not type(result) is str:
            await change_advert_info(advert_id=advert.id, posted_message_id=result.message_id, status='published',
                                     note='')


async def delete_advert_invoice_after_deadline(chat_id, message_id, advert_id):
    await change_advert_info(advert_id=advert_id, posted_message_id=-1, status='declined',
                             note='Истёк срок оплаты объявления!')
    await bot.delete_message(chat_id=chat_id, message_id=message_id)
    await bot.send_message(text='Срок оплаты истёк!', chat_id=chat_id)


async def bot_notify_moderators(text: str):
    moderators = await get_moderators()
    for counter, moderator in enumerate(moderators):
        scheduler.add_job(bot_send_message, trigger='date',
                          run_date=datetime.now(pytz.timezone('Europe/Moscow')) + timedelta(seconds=counter + 1),
                          id=f'notify_moderator_{moderator.id}',
                          kwargs={'to_chat': moderator.id, 'text': text})
