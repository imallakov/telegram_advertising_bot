import datetime
import calendar
from types import NoneType

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database.models import Chat, Tariff, User
from core.database.requests import get_all_chats, get_adverts_in_this_month, get_tariffs_of_chat, get_moderators
from core.keyboards.callbackdata import CalendarCallback, ChatsCallback, TariffCallback, ModeratorDecision, \
    ClientCabinet, AdminCabinet


async def inline_calendar_day_choice(chat_id: int, year: int = datetime.date.today().year,
                                     month: int = datetime.date.today().month) -> InlineKeyboardMarkup:
    months = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь',
              'Ноябрь', 'Декабрь']

    if month < 1:
        month = 1
    elif month > 12:
        month = 12

    if year < datetime.date.today().year:
        year = datetime.date.today().year
    elif year > datetime.date.today().year + 5:
        year = datetime.date.today().year + 5

    if year == datetime.date.today().year and month < datetime.date.today().month:
        month = datetime.date.today().month

    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text='⏪',
                             callback_data=CalendarCallback(event='new_date', year=year - 1, month=month).pack()),
        InlineKeyboardButton(text=f'{year}',
                             callback_data=CalendarCallback(event='choose_year', year=year, month=month).pack()),
        InlineKeyboardButton(text='⏩',
                             callback_data=CalendarCallback(event='new_date', year=year + 1, month=month).pack()),
    )
    builder.add(
        InlineKeyboardButton(text='⏪',
                             callback_data=CalendarCallback(event='new_date', year=year, month=month - 1).pack()),
        InlineKeyboardButton(text=f'{months[month]}',
                             callback_data=CalendarCallback(event='choose_month', year=year, month=month).pack()),
        InlineKeyboardButton(text='⏩',
                             callback_data=CalendarCallback(event='new_date', year=year, month=month + 1).pack()),
    )
    builder.adjust(3, repeat=True)

    month_days = InlineKeyboardBuilder()

    this_month = calendar.monthcalendar(year, month)
    month_days.add(
        InlineKeyboardButton(text='Пн', callback_data='week_days'),
        InlineKeyboardButton(text='Вт', callback_data='week_days'),
        InlineKeyboardButton(text='Ср', callback_data='week_days'),
        InlineKeyboardButton(text='Чт', callback_data='week_days'),
        InlineKeyboardButton(text='Пт', callback_data='week_days'),
        InlineKeyboardButton(text='Сб', callback_data='week_days'),
        InlineKeyboardButton(text='Вс', callback_data='week_days'),

    )
    chat_adverts: list[int] = await get_adverts_in_this_month(chat_id=chat_id, month=month, year=year)
    week_num = 0
    for week in this_month:
        for day in week:
            text: str = str(day)
            event: str = 'chosen_date'
            if day == 0:
                text = ' '
                event = 'choose_another'
            elif (day <= int(datetime.datetime.now().strftime("%d")) and month == int(
                    datetime.datetime.now().strftime("%m")) and year == int(datetime.datetime.now().strftime("%Y"))):
                text = '⚫'
                event = 'choose_another'
            elif day in chat_adverts:
                text = '⛔'
                event = 'choose_another'
            month_days.add(
                InlineKeyboardButton(text=text,
                                     callback_data=CalendarCallback(event=event, year=year, month=month,
                                                                    day=day).pack())
            )
            week_num += 1
    month_days.adjust(7, repeat=True)
    builder.attach(month_days)
    return builder.as_markup()


async def inline_calendar_year_choice(month: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    this_year = datetime.datetime.now().year
    for year in range(this_year, this_year + 6):
        builder.add(
            InlineKeyboardButton(text=str(year),
                                 callback_data=CalendarCallback(event='new_date', year=year, month=month).pack())
        )
    builder.adjust(3, repeat=True)
    return builder.as_markup()


async def inline_calendar_month_choice(year: int) -> InlineKeyboardMarkup:
    months = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь',
              'Ноябрь', 'Декабрь']

    builder = InlineKeyboardBuilder()

    for month in range(1, 13):
        builder.add(
            InlineKeyboardButton(text=months[month],
                                 callback_data=CalendarCallback(event='new_date', year=year, month=month).pack())
        )
    builder.adjust(3, repeat=True)
    return builder.as_markup()


async def chats_choice(index: int = 1) -> InlineKeyboardMarkup:
    chats: list[Chat] = await get_all_chats()

    builder = InlineKeyboardBuilder()
    chats_number = 4  # number of chats in one list
    for ind in range((index - 1) * chats_number, min(index * chats_number, len(chats))):
        builder.add(
            InlineKeyboardButton(
                text=chats[ind].name,
                callback_data=ChatsCallback(event='chat_id', param=chats[ind].id).pack()
            )
        )

    navigation = InlineKeyboardBuilder()

    if index > 1:
        navigation.add(
            InlineKeyboardButton(
                text='⏪',
                callback_data=ChatsCallback(event='index', param=index - 1).pack()
            )
        )

    if len(chats) - (index * chats_number) > 0:
        navigation.add(
            InlineKeyboardButton(
                text='⏩',
                callback_data=ChatsCallback(event='index', param=index + 1).pack()
            )
        )
    navigation.adjust(2, repeat=True)
    builder.adjust(1, repeat=True)
    builder.attach(navigation)
    return builder.as_markup()


async def chosen_chat(chat_username: str, chat_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text='Перейти на канал',
            url=f'https://t.me/{chat_username}'
        ),
        InlineKeyboardButton(
            text='Назад',
            callback_data=ChatsCallback(event='back_to_chat_choice', param=1).pack()
        ),
        InlineKeyboardButton(
            text='✅',
            callback_data=ChatsCallback(event='surely_chosen_chat', param=chat_id).pack()
        )
    )

    builder.adjust(1, 2)

    return builder.as_markup()


async def tariff_choice(chat_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    tariffs: list[Tariff] = await get_tariffs_of_chat(chat_id)
    for ind in range(len(tariffs)):
        tariff_id: int = tariffs[ind].id
        days: int = tariffs[ind].days
        price: int = tariffs[ind].price
        builder.add(
            InlineKeyboardButton(
                text=f'{days} дней({price}р)',
                callback_data=TariffCallback(event='chosen_tariff', tariff_id=tariff_id, days=days, price=price).pack()
            )
        )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def confirm_data() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=f'Создать объявление заново🔄️',
            callback_data='create_advert_again'
        ),
        InlineKeyboardButton(
            text=f'Отправить на модерацию✅',
            callback_data='create_advert',
        )
    )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def are_you_sure_delete(current_index: int, advert_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=f'Нет',
            callback_data=ClientCabinet(event='to_my_orders', index=current_index, status='status', note='').pack()
        ),
        InlineKeyboardButton(
            text=f'Да🗑️',
            callback_data=ClientCabinet(event='surely_delete_advert', index=current_index, status='status',
                                        note=str(advert_id)).pack(),
        )
    )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def after_client_deletes_advert(index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=f'Хорошо',
            callback_data=ClientCabinet(event='to_my_orders', index=index, status='status',
                                        note='after_delete_order').pack()
        )
    )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def markirovka_reklamy() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=f'Нет',
            callback_data='net_markirovki'
        ),
        InlineKeyboardButton(
            text=f'Да',
            callback_data='markirovka',
        )
    )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def moderator_menu(orders: int, questions: int, undeleted_adverts: int):
    builder = InlineKeyboardBuilder()
    if orders > 0:
        builder.add(
            InlineKeyboardButton(
                text='Заявки',
                callback_data='to_new_orders',
            )
        )
    if questions > 0:
        builder.add(
            InlineKeyboardButton(
                text='Вопросы',
                callback_data='to_new_questions',
            )
        )
    if undeleted_adverts > 0:
        builder.add(
            InlineKeyboardButton(
                text='Не удаленные объявления',
                callback_data='to_undeleted_adverts'
            )
        )
    builder.add(
        InlineKeyboardButton(
            text='Главное меню',
            callback_data='to_main_menu',
        )
    )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def to_next_question():
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text='След.вопрос',
            callback_data='to_new_questions',
        )
    )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def moderate_advert_keyboard(advert_id: id) -> InlineKeyboardMarkup:
    information = InlineKeyboardBuilder()
    information.add(
        InlineKeyboardButton(
            text='ℹ️Информация о заявке',
            callback_data=ModeratorDecision(decision='info', advert_id=advert_id).pack()
        ),
    )
    action = InlineKeyboardBuilder()
    action.add(
        InlineKeyboardButton(
            text='❌',
            callback_data=ModeratorDecision(decision='decline', advert_id=advert_id).pack()
        ),
        InlineKeyboardButton(
            text='✅',
            callback_data=ModeratorDecision(decision='approve', advert_id=advert_id).pack()
        )
    )
    menu = InlineKeyboardBuilder()
    menu.add(
        InlineKeyboardButton(
            text='Закончить модерацию',
            callback_data='to_moderator_cabinet'
        )
    )
    menu.adjust(1, repeat=True)
    action.attach(menu)
    information.attach(action)
    return information.as_markup()


async def advert_info_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Закрыть информацию',
            callback_data='delete_this_message'
        )
    )
    return builder.as_markup()


async def client_cabinet() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Мои Заявки',
            callback_data=ClientCabinet(event='to_my_orders', index=0, status='status', note='').pack()
        ),
        InlineKeyboardButton(
            text='Главное меню',
            callback_data=ClientCabinet(event='to_main_menu', index=0, status='status', note='').pack()
        ),
    )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def my_orders_keyboard(current_index: int, length: int, advert_id, advert_status, note: str):
    information = InlineKeyboardBuilder()
    information.add(
        InlineKeyboardButton(
            text='Информацияℹ️',
            callback_data=ClientCabinet(event='info', index=advert_id, status=advert_status, note=note).pack()
        )
    )
    control = InlineKeyboardBuilder()
    if current_index > 0:
        control.add(
            InlineKeyboardButton(
                text='⬅️',
                callback_data=ClientCabinet(event='to_my_orders', index=current_index - 1, status='status',
                                            note='').pack()
            )
        )
    if current_index < length - 1:
        control.add(
            InlineKeyboardButton(
                text='➡️',
                callback_data=ClientCabinet(event='to_my_orders', index=current_index + 1, status='status',
                                            note='').pack()
            )
        )
    control.adjust(2, repeat=True)
    general = InlineKeyboardBuilder()
    general.add(
        InlineKeyboardButton(
            text='Удалить заявку',
            callback_data=ClientCabinet(event='delete_order', index=advert_id, status=advert_status,
                                        note=str(current_index)).pack()
        ),
        InlineKeyboardButton(
            text='Назад в кабинет',
            callback_data=ClientCabinet(event='to_client_cabinet', index=0, status='status', note='').pack()
        )
    )
    general.adjust(1, repeat=True)
    information.attach(control)
    information.attach(general)
    return information.as_markup()


async def surely_decline_keyboard(advert_id) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Да, Отказать!',
            callback_data=ModeratorDecision(decision='surely_decline', advert_id=advert_id).pack()
        )
    )
    return builder.as_markup()


async def admin_cabinet_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Каналы/чаты',
            callback_data=AdminCabinet(event='to_chats', index=0, note='').pack()
        ),
        InlineKeyboardButton(
            text='Модераторы',
            callback_data=AdminCabinet(event='to_moderators', index=0, note='').pack()
        ),
        InlineKeyboardButton(
            text='Главное меню',
            callback_data=AdminCabinet(event='to_main_menu', index=0, note='').pack()
        )
    )
    builder.adjust(1, True)
    return builder.as_markup()


async def admin_list_of_chats(index: int = 1) -> InlineKeyboardMarkup:
    chats: list[Chat] = await get_all_chats()

    builder = InlineKeyboardBuilder()
    chats_number = 4  # number of chats in one list
    for ind in range((index - 1) * chats_number, min(index * chats_number, len(chats))):
        if type(chats[ind].username) is NoneType or type(chats[ind].username) is None:
            chats[ind].username = ''
        builder.add(
            InlineKeyboardButton(
                text=chats[ind].name,
                callback_data=AdminCabinet(event='to_chat_with_id', index=chats[ind].id,
                                           note=chats[ind].username).pack()
            ),
            InlineKeyboardButton(
                text='❌',
                callback_data=AdminCabinet(event='delete_chat', index=chats[ind].id, note=chats[ind].username).pack()
            )
        )

    navigation = InlineKeyboardBuilder()

    if index > 1:
        navigation.add(
            InlineKeyboardButton(
                text='⏪',
                callback_data=AdminCabinet(event='index', index=index - 1, note='').pack()
            )
        )

    if len(chats) - (index * chats_number) > 0:
        navigation.add(
            InlineKeyboardButton(
                text='⏩',
                callback_data=AdminCabinet(event='index', index=index + 1, note='').pack()
            )
        )
    menu = InlineKeyboardBuilder()
    menu.add(
        InlineKeyboardButton(
            text='Добавить канал/чат➕',
            callback_data=AdminCabinet(event='add_new_chat', index=0, note='').pack()
        ),
        InlineKeyboardButton(
            text='Назад',
            callback_data=AdminCabinet(event='to_admin_cabinet', index=0, note='').pack()
        )
    )
    navigation.adjust(2, repeat=True)
    builder.adjust(2, repeat=True)
    menu.adjust(1, repeat=True)
    builder.attach(navigation)
    builder.attach(menu)
    return builder.as_markup()


async def admin_tariffs_of_chat(chat_id: int, chat_username: str) -> InlineKeyboardMarkup:
    tariffs: list[Tariff] = await get_tariffs_of_chat(chat_id)
    if chat_username == '':
        chat_username = tariffs[0].chat.username
    mainkb = InlineKeyboardBuilder()
    mainkb.add(
        InlineKeyboardButton(
            text='Перейти на канал',
            url=f't.me/{chat_username}'
        )
    )
    builder = InlineKeyboardBuilder()
    for ind in range(len(tariffs)):
        tariff_id: int = tariffs[ind].id
        days: int = tariffs[ind].days
        price: int = tariffs[ind].price
        builder.add(
            InlineKeyboardButton(
                text=f'{days} дней({price}р)',
                callback_data='nothing'
            ),
            InlineKeyboardButton(
                text=f'❌',
                callback_data=AdminCabinet(event='delete_tariff', index=tariff_id, note=str(chat_id)).pack()
            )
        )
    menu = InlineKeyboardBuilder()
    menu.add(
        InlineKeyboardButton(
            text='Добавить тарифф➕',
            callback_data=AdminCabinet(event='add_new_tariff', index=chat_id, note=chat_username).pack()
        ),
        InlineKeyboardButton(
            text='Назад',
            callback_data=AdminCabinet(event='to_chats', index=0, note='').pack()
        )
    )
    menu.adjust(1, repeat=True)
    builder.adjust(2, repeat=True)
    builder.attach(menu)
    mainkb.attach(builder)
    return mainkb.as_markup()


async def are_you_sure_deleting_chat(chat_id: int, chat_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Нет❌',
            callback_data=AdminCabinet(event='to_chats', index=0, note='').pack()
        ),
        InlineKeyboardButton(
            text='Да🗑️',
            callback_data=AdminCabinet(event='surely_delete_chat', index=chat_id, note=chat_username).pack()
        )
    )
    builder.adjust(2, True)
    return builder.as_markup()


async def admin_list_of_moderators() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    moderators: list[User] = await get_moderators()
    for moderator in moderators:
        builder.add(
            InlineKeyboardButton(
                text=f'{moderator.full_name} ( @{moderator.username} )',
                url=f't.me/{moderator.username}'
            ),
            InlineKeyboardButton(
                text='❌',
                callback_data=AdminCabinet(event='delete_moderator', index=moderator.id, note=moderator.username).pack()
            ),
        )
    menu = InlineKeyboardBuilder()
    menu.add(
        InlineKeyboardButton(
            text='Добавить модератора➕',
            callback_data=AdminCabinet(event='add_new_moderator', index=0, note='').pack()
        ),
        InlineKeyboardButton(
            text='Назад',
            callback_data=AdminCabinet(event='to_admin_cabinet', index=0, note='').pack()
        )
    )
    builder.adjust(2, repeat=True)
    menu.adjust(1, repeat=True)
    builder.attach(menu)
    return builder.as_markup()


async def are_you_sure_deleting_moderator(user_id: int, user_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Нет❌',
            callback_data=AdminCabinet(event='to_moderators', index=0, note='').pack()
        ),
        InlineKeyboardButton(
            text='Да🗑️',
            callback_data=AdminCabinet(event='surely_delete_moderator', index=user_id, note=user_username).pack()
        )
    )
    builder.adjust(2, True)
    return builder.as_markup()


async def after_adding_new_tariff_keyboard(chat_id: int, chat_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Хорошо👍',
            callback_data=AdminCabinet(event='to_chat_with_id', index=chat_id, note=chat_username).pack()
        )
    )
    return builder.as_markup()


async def after_adding_new_chat_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Хорошо👍',
            callback_data=AdminCabinet(event='to_chats', index=0, note='').pack()
        ),
    )
    return builder.as_markup()


async def after_adding_new_moderator_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Хорошо👍',
            callback_data=AdminCabinet(event='to_moderators', index=0, note='').pack()
        ),
    )
    return builder.as_markup()


async def deleting_undeleted_adverts() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Все удалены👍🏻',
            callback_data="after_deleting_undeleted_adverts"
        ),
        InlineKeyboardButton(
            text='Назад',
            callback_data="to_moderator_cabinet"
        ),
    )
    return builder.as_markup()


async def inline_cancel_button(data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Отменить',
            callback_data=data
        )
    )
    return builder.as_markup()


async def check_organisation_name_by_inn(is_found: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Изменить ИНН',
            callback_data='enter_inn_again'
        ),
        InlineKeyboardButton(
            text='Вводить назв.орг. вручную',
            callback_data='enter_org_name'
        )
    )
    if is_found:
        builder.add(
            InlineKeyboardButton(
                text='Да правильно✅',
                callback_data='correct_organisation_name'
            )
        )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def advert_payment_keyboard(user_id: int, advert_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text='Оплатить с карты💳',
            pay=True
        ),
        InlineKeyboardButton(
            text='Списать с баланса',
            callback_data=f'balance_pay:{user_id}|{advert_id}',

        )
    )
    builder.adjust(1, repeat=True)
    print(builder)
    return builder.as_markup()
