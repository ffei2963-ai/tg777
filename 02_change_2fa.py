#!/usr/bin/env python3
"""
操作 2: 修改 2FA 密码
====================
批量修改 Telegram 账号的两步验证密码。
通过 Telethon MTProto API 直接操作，不需要 Desktop。

用法:
    python 02_change_2fa.py <旧密码> <新密码> [账号ID列表]

示例:
    python 02_change_2fa.py 0369 112211 9 10 11
    python 02_change_2fa.py oldpw newpw           # 修改全部账号
    python 02_change_2fa.py oldpw newpw --db my.db
"""

import os
import sys
import asyncio
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.database import Database
from lib.telethon_helper import DEFAULT_API_ID, DEFAULT_API_HASH
from telethon import TelegramClient


def change_2fa(session_path: str, phone: str, old_password: str,
               new_password: str, db_password: str = "") -> dict:
    """修改单个账号的 2FA 密码"""

    client = TelegramClient(os.path.splitext(session_path)[0], DEFAULT_API_ID, DEFAULT_API_HASH)

    async def _do():
        await client.connect()
        try:
            pwd = db_password or ""
            await client.start(phone=phone, password=pwd if pwd else None)
        except Exception as e:
            await client.disconnect()
            return {"success": False, "error": f"登录失败: {e}"}

        me = await client.get_me()
        try:
            old = old_password or pwd
            result = await client.edit_2fa(
                current_password=old,
                new_password=new_password,
                hint="tg777",
            )
            await client.disconnect()
            return {"success": True, "phone": me.phone, "name": me.first_name}
        except Exception as e:
            await client.disconnect()
            return {"success": False, "error": str(e)}

    return asyncio.run(_do())


def main():
    parser = argparse.ArgumentParser(description="批量修改 Telegram 账号 2FA 密码")
    parser.add_argument("old_password", help="旧密码")
    parser.add_argument("new_password", help="新密码")
    parser.add_argument("account_ids", nargs="*", type=int, help="账号ID列表 (不填则修改全部)")
    parser.add_argument("--db", default="data/tg777.db", help="数据库路径")
    args = parser.parse_args()

    db = Database(args.db)
    accounts = db.list_accounts()
    if not accounts:
        print("数据库中没有账号，请先运行 01_import_accounts.py")
        return

    if args.account_ids:
        accounts = [a for a in accounts if a["id"] in args.account_ids]
        if not accounts:
            print(f"找不到指定账号: {args.account_ids}")
            return

    print(f"修改 2FA 密码: {args.old_password} → {args.new_password}")
    print(f"目标账号: {len(accounts)} 个\n")

    success = 0
    for acc in accounts:
        sp = acc["session_path"]
        if not os.path.isfile(sp):
            print(f"  [{acc['id']}] ❌ session 文件不存在: {sp}")
            continue
        print(f"  [{acc['id']}] {acc['phone']} ... ", end="", flush=True)
        r = change_2fa(sp, acc["phone"], args.old_password, args.new_password,
                       acc.get("twofa_password", ""))
        if r["success"]:
            db.update_account(acc["id"], twofa_password=args.new_password)
            print(f"✅ {r['name']}")
            success += 1
        else:
            print(f"❌ {r['error']}")

    print(f"\n完成: {success}/{len(accounts)} 成功")


if __name__ == "__main__":
    main()
