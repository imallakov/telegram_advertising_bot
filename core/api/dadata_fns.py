import asyncio

from dadata import DadataAsync

from bot import bot_send_error_message
from config_reader import config

token = str(config.dadata_token.get_secret_value())
secret = str(config.dadata_secret_key.get_secret_value())


async def get_organisation_by_inn(inn: str) -> dict | None:
    try:
        async with DadataAsync(token, secret) as dadata:
            organisations = await dadata.find_by_id(name="party", query=inn)
        if len(organisations) == 0:
            return None
        else:
            return organisations[0]
    except Exception as error:
        print(error)
        await bot_send_error_message(text=f'get_organisation_by_inn:\nINN={inn}\nError:{error}')
