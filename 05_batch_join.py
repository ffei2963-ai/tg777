#!/usr/bin/env python3
"""
操作 5: 批量进群
================
通过 Telegram 群组链接批量加入群组。
支持公开群 (t.me/xxx) 和私密群 (t.me/+hash)。
每个账号间有可配置的延时，防止 flood wait。

用法:
    python 05_batch_join.py <链接> [账号ID列表] [--delay 0.5]

示例:
    python 05_batch_join.py "https://t.me/+t2D7VX2fkB4xNThh" 9 10 11
    python 05_batch_join.py "t.me/testgroup" --delay 1
    python 05_batch_join.py "+t2D7VX2fkB4xNThh"        # 全部账号
"""

import os
import sys
import asyncio
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.database import Database
from lib.telethon_helper import DEFAULT_API_ID, DEFAULT_API_HASH
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest


def join_group(session_path: str, phone: str, link: str, password: str = "") -> dict:
    client = TelegramClient(os.path.splitext(session_path)[0], DEFAULT_API_ID, DEFAULT_API_HASH)

    async def _do():
        await client.connect()
        try:
            await client.start(phone=phone, password=password or None)
        except Exception as e:
            await client.disconnect()
            return {"success": False, "error": f"登录失败: {e}"}

        try:
            if link.startswith("https://t.me/+"):
                await client(ImportChatInviteRequest(link.split("+")[-1]))
            elif link.startswith("+"):
                await client(ImportChatInviteRequest(link[1:]))
            elif link.startswith("https://t.me/") or link.startswith("t.me/"):
                username = link.replace("https://t.me/", "").replace("t.me/", "").strip("/")
                await client(JoinChannelRequest(username))
            else:
                await client(JoinChannelRequest(link))

            await client.disconnect()
            return {"success": True}
        except Exception as e:
            await client.disconnect()
            return {"success": False, "error": str(e)}

    return asyncio.run(_do())


def main():
    parser = argparse.ArgumentParser(description="批量通过链接加入 Telegram 群组")
    parser.add_argument("link", help="群组链接 (https://t.me/+hash 或 t.me/username)")
    parser.add_argument("account_ids", nargs="*", type=int, help="账号ID列表 (不填=全部)")
    parser.add_argument("--delay", type=float, default=0.5, help="账号间延时秒数 (默认0.5)")
    parser.add_argument("--db", default="data/tg777.db", help="数据库路径")
    args = parser.parse_args()

    db = Database(args.db)
    accounts = db.list_accounts()
    if not accounts:
        print("数据库中没有账号，请先运行 01_import_accounts.py")
        return

    if args.account_ids:
        accounts = [a for a in accounts if a["id"] in args.account_ids]

    print(f"进群: {args.link}")
    print(f"账号: {len(accounts)} 个 | 延时: {args.delay}秒\n")

    success = 0
    for i, acc in enumerate(accounts):
        if i > 0:
            import time
            time.sleep(args.delay)

        sp = acc["session_path"]
        if not os.path.isfile(sp):
            print(f"  [{acc['id']}] ❌ session 不存在")
            continue

        print(f"  [{acc['id']}] {acc['phone']} ... ", end="", flush=True)
        r = join_group(sp, acc["phone"], args.link, acc.get("twofa_password", ""))

        if r["success"]:
            print("✅ 已加入")
            success += 1
        else:
            err = r.get("error", "")
            if "already" in err.lower():
                print("⏭ 已在群中")
                success += 1
            else:
                print(f"❌ {err[:80]}")

    print(f"\n完成: {success}/{len(accounts)} 成功")


if __name__ == "__main__":
    main()
