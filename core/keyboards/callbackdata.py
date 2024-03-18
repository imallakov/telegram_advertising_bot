from aiogram.filters.callback_data import CallbackData


class CalendarCallback(CallbackData, prefix='calendar'):
    event: str
    year: int
    month: int
    day: int = 0


class ChatsCallback(CallbackData, prefix='chats'):
    event: str
    param: int


class TariffCallback(CallbackData, prefix='tariffs'):
    event: str
    tariff_id: int
    days: int
    price: int


class ModeratorDecision(CallbackData, prefix='moderation'):
    decision: str
    advert_id: int


class ClientCabinet(CallbackData, prefix='client'):
    event: str
    index: int
    status: str
    note: str


class AdminCabinet(CallbackData, prefix='admin'):
    event: str
    index: int
    note: str
