#!/usr/bin/env python3
"""
操作 4: 修改头像
================
批量修改 Telegram 账号的头像。
通过 Telethon UploadProfilePhotoRequest API 操作。

用法:
    python 04_change_avatar.py <图片路径> [账号ID列表]

示例:
    python 04_change_avatar.py photo1.jpg 9
    python 04_change_avatar.py avatar.png 10 11
    python 04_change_avatar.py new.jpg             # 修改全部账号
"""

import os
import sys
import asyncio
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.database import Database
from lib.telethon_helper import DEFAULT_API_ID, DEFAULT_API_HASH
from telethon import TelegramClient
from telethon.tl.functions.photos import UploadProfilePhotoRequest


def change_avatar(session_path: str, phone: str, image_path: str,
                  password: str = "") -> dict:
    """修改单个账号的头像"""

    client = TelegramClient(os.path.splitext(session_path)[0], DEFAULT_API_ID, DEFAULT_API_HASH)

    async def _do():
        await client.connect()
        try:
            await client.start(phone=phone, password=password or None)
        except Exception as e:
            await client.disconnect()
            return {"success": False, "error": f"登录失败: {e}"}

        try:
            uploaded = await client.upload_file(image_path, part_size_kb=512)
            await client(UploadProfilePhotoRequest(
                file=uploaded, video=None, video_start_ts=None,
            ))
            me = await client.get_me()
            await client.disconnect()
            return {"success": True, "phone": me.phone, "name": me.first_name}
        except Exception as e:
            await client.disconnect()
            return {"success": False, "error": str(e)}

    return asyncio.run(_do())


def main():
    parser = argparse.ArgumentParser(description="批量修改 Telegram 账号头像")
    parser.add_argument("image", help="头像图片路径 (JPEG/PNG)")
    parser.add_argument("account_ids", nargs="*", type=int, help="账号ID列表")
    parser.add_argument("--db", default="data/tg777.db", help="数据库路径")
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"错误: 找不到图片文件 {args.image}")
        return

    db = Database(args.db)
    accounts = db.list_accounts()
    if not accounts:
        print("数据库中没有账号")
        return

    if args.account_ids:
        accounts = [a for a in accounts if a["id"] in args.account_ids]
        if not accounts:
            print(f"找不到指定账号: {args.account_ids}")
            return

    print(f"头像文件: {args.image} ({os.path.getsize(args.image)} bytes)")
    print(f"目标: {len(accounts)} 个账号\n")

    success = 0
    for acc in accounts:
        sp = acc["session_path"]
        if not os.path.isfile(sp):
            print(f"  [{acc['id']}] ❌ session 不存在")
            continue
        print(f"  [{acc['id']}] {acc['phone']} ... ", end="", flush=True)
        r = change_avatar(sp, acc["phone"], args.image, acc.get("twofa_password", ""))
        if r["success"]:
            print(f"✅ {r['name']}")
            success += 1
        else:
            print(f"❌ {r['error']}")

    print(f"\n完成: {success}/{len(accounts)} 成功")


if __name__ == "__main__":
    main()
