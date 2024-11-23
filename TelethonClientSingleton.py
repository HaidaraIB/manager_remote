from telethon import TelegramClient
import os


class TelethonClientSingleton(TelegramClient):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:

            cls._instance = TelegramClient(
                session="telethon_session",
                api_id=int(os.getenv("API_ID")),
                api_hash=os.getenv("API_HASH"),
            ).start(bot_token=os.getenv("BOT_TOKEN"))
        return cls._instance
