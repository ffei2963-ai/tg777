#!/usr/bin/env python3
"""
操作 6: 一键退出所有群组
========================
批量退出指定账号的全部群组。
遍历对话列表，逐一退出所有群组和频道。

用法:
    python 06_batch_leave.py [账号ID列表] [--delay 0.5]

示例:
    python 06_batch_leave.py 9 10 11
    python 06_batch_leave.py                      # 退出全部账号的全部群
    python 06_batch_leave.py --delay 1 9
"""

import os
import sys
import asyncio
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.database import Database
from lib.telethon_helper import DEFAULT_API_ID, DEFAULT_API_HASH
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import DeleteChatUserRequest


def leave_all_groups(session_path: str, phone: str, password: str = "",
                     delay: float = 0.3) -> dict:
    client = TelegramClient(os.path.splitext(session_path)[0], DEFAULT_API_ID, DEFAULT_API_HASH)

    async def _do():
        await client.connect()
        try:
            await client.start(phone=phone, password=password or None)
        except Exception as e:
            await client.disconnect()
            return {"success": False, "error": f"登录失败: {e}"}

        try:
            dialogs = await client.get_dialogs(limit=200)
            groups = [(d.name, d.entity) for d in dialogs if d.is_group or d.is_channel]

            left = []
            for name, entity in groups:
                if isinstance(entity, Channel):
                    await client(LeaveChannelRequest(entity))
                elif isinstance(entity, Chat):
                    me = await client.get_me()
                    await client(DeleteChatUserRequest(chat_id=entity.id, user_id=me))
                else:
                    try:
                        await client(LeaveChannelRequest(entity))
                    except Exception:
                        me = await client.get_me()
                        await client(DeleteChatUserRequest(chat_id=entity.id, user_id=me))
                left.append(name)
                await asyncio.sleep(delay)

            await client.disconnect()
            return {"success": True, "groups_left": left, "count": len(left)}
        except Exception as e:
            await client.disconnect()
            return {"success": False, "error": str(e)}

    return asyncio.run(_do())


def main():
    parser = argparse.ArgumentParser(description="一键退出全部群组")
    parser.add_argument("account_ids", nargs="*", type=int, help="账号ID列表 (不填=全部)")
    parser.add_argument("--delay", type=float, default=0.3, help="群组间延时 (默认0.3秒)")
    parser.add_argument("--db", default="data/tg777.db", help="数据库路径")
    args = parser.parse_args()

    db = Database(args.db)
    accounts = db.list_accounts()
    if not accounts:
        print("没有账号")
        return

    if args.account_ids:
        accounts = [a for a in accounts if a["id"] in args.account_ids]

    print(f"退出全部群组: {len(accounts)} 个账号\n")

    total_left = 0
    for acc in accounts:
        sp = acc["session_path"]
        if not os.path.isfile(sp):
            print(f"  [{acc['id']}] ❌ session 不存在")
            continue

        print(f"  [{acc['id']}] {acc['phone']} ... ", end="", flush=True)
        r = leave_all_groups(sp, acc["phone"], acc.get("twofa_password", ""), args.delay)

        if r["success"]:
            count = r["count"]
            groups = r.get("groups_left", [])
            print(f"✅ 退出 {count} 个群")
            for g in groups:
                print(f"      - {g}")
            total_left += count
        else:
            print(f"❌ {r.get('error', '?')[:80]}")

    print(f"\n总计退出: {total_left} 个群组")


if __name__ == "__main__":
    main()
