#!/usr/bin/env python3
"""
操作 5: 批量进群 (拟人随机延时)
=================================
通过 Telegram 群组链接批量加入群组，账号间随机延时模拟真人。
支持公开群 (t.me/xxx) 和私密群 (t.me/+hash)。

用法:
    python 05_batch_join.py <链接> [账号ID] [--min 0.8] [--max 3.5]

示例:
    python 05_batch_join.py "https://t.me/+hash" 9 10 11
    python 05_batch_join.py "t.me/testgroup" --min 2 --max 8
"""

import os, sys, asyncio, argparse, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.database import Database
from lib.telethon_helper import DEFAULT_API_ID, DEFAULT_API_HASH, human_delay
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest


def join_group(session_path, phone, link, password=""):
    client = TelegramClient(os.path.splitext(session_path)[0], DEFAULT_API_ID, DEFAULT_API_HASH)
    async def _do():
        await client.connect()
        try:
            await client.start(phone=phone, password=password or None)
        except Exception as e:
            await client.disconnect(); return {"success": False, "error": str(e)}
        try:
            if link.startswith("https://t.me/+"):
                await client(ImportChatInviteRequest(link.split("+")[-1]))
            elif link.startswith("+"):
                await client(ImportChatInviteRequest(link[1:]))
            elif link.startswith("https://t.me/") or link.startswith("t.me/"):
                await client(JoinChannelRequest(link.replace("https://t.me/","").replace("t.me/","").strip("/")))
            else:
                await client(JoinChannelRequest(link))
            await client.disconnect(); return {"success": True}
        except Exception as e:
            await client.disconnect(); return {"success": False, "error": str(e)}
    return asyncio.run(_do())


def main():
    p = argparse.ArgumentParser(description="批量进群 (随机延时)")
    p.add_argument("link", help="群组链接")
    p.add_argument("account_ids", nargs="*", type=int, help="账号ID")
    p.add_argument("--min", type=float, default=0.8, help="最小延时(秒)")
    p.add_argument("--max", type=float, default=3.5, help="最大延时(秒)")
    p.add_argument("--db", default="data/tg777.db")
    args = p.parse_args()

    db = Database(args.db)
    accounts = db.list_accounts()
    if not accounts: print("无账号"); return
    if args.account_ids: accounts = [a for a in accounts if a["id"] in args.account_ids]

    print(f"进群: {args.link}")
    print(f"账号: {len(accounts)}个 | 随机延时: {args.min}~{args.max}秒\n")

    ok = 0
    for i, acc in enumerate(accounts):
        if i > 0:
            d = human_delay(args.min, args.max)
            print(f"  ⏱ 等待 {d:.1f}s ...")
            time.sleep(d)

        sp = acc["session_path"]
        if not os.path.isfile(sp):
            print(f"  [{acc['id']}] ❌ session 不存在"); continue
        print(f"  [{acc['id']}] {acc['phone']} ... ", end="", flush=True)
        r = join_group(sp, acc["phone"], args.link, acc.get("twofa_password", ""))
        if r["success"]: print("✅"); ok += 1
        elif "already" in str(r.get("error","")).lower(): print("⏭ 已在"); ok += 1
        else: print(f"❌ {r.get('error','')[:60]}")

    print(f"\n{ok}/{len(accounts)} 成功")


if __name__ == "__main__":
    main()
