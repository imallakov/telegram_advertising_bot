from aiogram.types import Chat, InlineKeyboardMarkup, Message

from config_reader import config
from aiogram import Bot

bot = Bot(token=config.bot_token.get_secret_value())


async def can_post_in_chat(chat_id: int | str) -> str:
    try:
        chat = await bot.get_chat(chat_id)
        membership = await bot.get_chat_member(chat_id, bot.id)
        if chat.type == 'channel':
            return 'success' if membership.status == membership.status.ADMINISTRATOR else 'channel_not_admin'
        else:
            return 'success' if membership.status == membership.status.MEMBER or membership.status == membership.status.ADMINISTRATOR else 'not_member'
    except Exception as error:
        await bot_send_error_message('can_post_in_chat ' + '\nchat_id=' + chat_id + '\nError: ' + error.__str__())
        return 'error'


async def get_chat_by_username_from_telegram(chat_id: str | int) -> Chat | str:
    try:
        return await bot.get_chat(chat_id)
    except Exception as error:
        await bot_send_error_message(
            'get_chat_by_username_from_telegram ' + '\nchat_id = ' + chat_id + '\nError:' + error.__str__())
        return 'error'


async def get_member_count(chat_id: str | int) -> int:
    try:
        return await bot.get_chat_member_count(chat_id)
    except Exception as error:
        await bot_send_error_message(text='get_member_count: ' + error.__str__())
        return 0


async def bot_edit_message_text_in_chat(chat_id: int, message_id: int, new_text: str, reply_markup=None) -> str:
    try:
        await bot.edit_message_text(text=new_text, chat_id=chat_id, message_id=message_id,
                                    reply_markup=reply_markup)
        return 'success'
    except Exception as error:
        await bot_send_error_message(
            'bot_edit_message_text_in_chat:\nchat_id=' + str(chat_id) + '\nmessage_id=' + str(
                message_id) + '\nnew_text=' + new_text + error.__str__())
        return 'error'


async def bot_delete_message_from_chat(chat_id: int, message_id: int) -> str:
    try:
        await bot.delete_message(chat_id, message_id)
        return 'success'
    except Exception as error:
        await bot_send_error_message('bot_delete_messsage_from_chat:\nchat_id=' + str(chat_id) + '\nmessage_id=' + str(
            message_id) + error.__str__())
        return 'error'


async def bot_send_message(to_chat: int, text: str) -> Message | None:
    try:
        return await bot.send_message(chat_id=to_chat, text=text)
    except Exception as error:
        await bot_send_error_message(
            f'bot_send_message: error sending message to_chat={to_chat} Error:{error.__str__()}')
        return None


async def bot_send_error_message(text: str):
    try:
        return await bot.send_message(chat_id='-1002077750505', text=text)
    except Exception as error:
        print(f'error sending error message: {text}   to chat, sending error: ', error.__str__())


async def bot_post_advert(media_id, media_type, chat_id, chat_type, text) -> Message | str:
    try:
        if media_type == 'photo':
            sent_message = await bot.send_photo(chat_id=chat_id, photo=media_id, caption=text)
        else:
            sent_message = await bot.send_video(chat_id=chat_id, video=media_id, caption=text)
        if chat_type == 'group':
            await bot.pin_chat_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id,
                                       disable_notification=True)
        return sent_message
    except Exception as error:
        await bot_send_error_message(
            f'bot_post_advert: media_id={media_id} media_type={media_type} chat_id={chat_id} '
            f'text={text} Error: {error.__str__()}')
        return 'error'