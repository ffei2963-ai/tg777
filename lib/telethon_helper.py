"""Telethon 辅助函数"""

import os
import asyncio
import random
from telethon import TelegramClient

DEFAULT_API_ID = 6
DEFAULT_API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"


def human_delay(min_sec: float = 0.8, max_sec: float = 3.5) -> float:
    """拟人随机延时 (默认 0.8~3.5 秒)"""
    return round(random.uniform(min_sec, max_sec), 2)


def connect_account(session_path: str, phone: str, password: str = "",
                    api_id: int = DEFAULT_API_ID, api_hash: str = DEFAULT_API_HASH):
    session_name = os.path.splitext(session_path)[0]
    client = TelegramClient(session_name, api_id, api_hash)

    async def _do():
        await client.connect()
        await client.start(phone=phone, password=password or None)
        return client

    return asyncio.run(_do())


def get_me(session_path: str):
    client = TelegramClient(os.path.splitext(session_path)[0], DEFAULT_API_ID, DEFAULT_API_HASH)

    async def _do():
        await client.connect()
        await client.start()
        me = await client.get_me()
        await client.disconnect()
        return {"id": me.id, "phone": me.phone, "first_name": me.first_name,
                "last_name": me.last_name, "username": me.username}

    return asyncio.run(_do())
