#!/usr/bin/env python3
"""
操作 3: 修改名字 (First Name / Last Name)
===========================================
批量修改 Telegram 账号的显示名字。
通过 Telethon UpdateProfileRequest API 操作。

用法:
    python 03_change_name.py <新名字> [账号ID列表]

示例:
    python 03_change_name.py "Zhang Ning" 9 11
    python 03_change_name.py "Mary" 10
    python 03_change_name.py "Marketing"             # 修改全部账号
    python 03_change_name.py "John" --last "Doe" 1 2 # 同时改姓和名
"""

import os
import sys
import asyncio
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.database import Database
from lib.telethon_helper import DEFAULT_API_ID, DEFAULT_API_HASH
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateProfileRequest


def change_name(session_path: str, phone: str, first_name: str,
                last_name: str = "", password: str = "") -> dict:
    """修改单个账号的名字"""

    client = TelegramClient(os.path.splitext(session_path)[0], DEFAULT_API_ID, DEFAULT_API_HASH)

    async def _do():
        await client.connect()
        try:
            await client.start(phone=phone, password=password or None)
        except Exception as e:
            await client.disconnect()
            return {"success": False, "error": f"登录失败: {e}"}

        try:
            await client(UpdateProfileRequest(
                first_name=first_name,
                last_name=last_name,
            ))
            me = await client.get_me()
            await client.disconnect()
            return {"success": True, "phone": me.phone,
                    "new_name": f"{me.first_name} {me.last_name}".strip()}
        except Exception as e:
            await client.disconnect()
            return {"success": False, "error": str(e)}

    return asyncio.run(_do())


def get_current_names(db_path: str) -> list[dict]:
    """获取所有账号的当前名字"""
    db = Database(db_path)
    accounts = db.list_accounts()
    results = []
    for acc in accounts:
        sp = acc["session_path"]
        if not os.path.isfile(sp):
            continue
        client = TelegramClient(os.path.splitext(sp)[0], DEFAULT_API_ID, DEFAULT_API_HASH)

        async def _get():
            await client.connect()
            await client.start(phone=acc["phone"], password=acc.get("twofa_password", ""))
            me = await client.get_me()
            await client.disconnect()
            return me

        me = asyncio.run(_get())
        results.append({"id": acc["id"], "phone": me.phone,
                        "first_name": me.first_name, "last_name": me.last_name or ""})
        print(f"  [{acc['id']}] +{me.phone} → {me.first_name} {me.last_name or ''}")

    return results


def main():
    parser = argparse.ArgumentParser(description="批量修改 Telegram 账号名字")
    parser.add_argument("first_name", help="新名字 (First Name)")
    parser.add_argument("--last", default="", help="姓氏 (Last Name), 留空则清空")
    parser.add_argument("account_ids", nargs="*", type=int, help="账号ID列表 (不填则修改全部)")
    parser.add_argument("--db", default="data/tg777.db", help="数据库路径")
    parser.add_argument("--show", action="store_true", help="仅显示当前名字，不修改")
    args = parser.parse_args()

    db = Database(args.db)
    accounts = db.list_accounts()
    if not accounts:
        print("数据库中没有账号")
        return

    if args.show:
        print("当前账号名字:")
        get_current_names(args.db)
        return

    if args.account_ids:
        accounts = [a for a in accounts if a["id"] in args.account_ids]
        if not accounts:
            print(f"找不到指定账号: {args.account_ids}")
            return

    print(f"修改名字: → {args.first_name} {args.last_name}")
    print(f"目标: {len(accounts)} 个账号\n")

    success = 0
    for acc in accounts:
        sp = acc["session_path"]
        if not os.path.isfile(sp):
            print(f"  [{acc['id']}] ❌ session 不存在")
            continue
        print(f"  [{acc['id']}] {acc['phone']} ... ", end="", flush=True)
        r = change_name(sp, acc["phone"], args.first_name, args.last,
                        acc.get("twofa_password", ""))
        if r["success"]:
            print(f"✅ → {r['new_name']}")
            success += 1
        else:
            print(f"❌ {r['error']}")

    print(f"\n完成: {success}/{len(accounts)} 成功")


if __name__ == "__main__":
    main()
