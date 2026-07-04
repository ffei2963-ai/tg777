#!/usr/bin/env python3
"""
操作 6: 一键退出所有群组 (拟人随机延时)
========================================
批量退出指定账号的全部群组，群组间和账号间均随机延时。

用法:
    python 06_batch_leave.py [账号ID] [--min 0.8] [--max 3.5]

示例:
    python 06_batch_leave.py 9 10 11
    python 06_batch_leave.py --min 2 --max 6
"""

import os, sys, asyncio, argparse, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.database import Database
from lib.telethon_helper import DEFAULT_API_ID, DEFAULT_API_HASH, human_delay
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import DeleteChatUserRequest


def leave_all(session_path, phone, password="", delay_min=0.3, delay_max=1.5):
    client = TelegramClient(os.path.splitext(session_path)[0], DEFAULT_API_ID, DEFAULT_API_HASH)
    async def _do():
        await client.connect()
        try: await client.start(phone=phone, password=password or None)
        except Exception as e: await client.disconnect(); return {"success": False, "error": str(e)}
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
                    try: await client(LeaveChannelRequest(entity))
                    except:
                        me = await client.get_me()
                        await client(DeleteChatUserRequest(chat_id=entity.id, user_id=me))
                left.append(name)
                await asyncio.sleep(human_delay(delay_min, delay_max))
            await client.disconnect()
            return {"success": True, "groups_left": left, "count": len(left)}
        except Exception as e: await client.disconnect(); return {"success": False, "error": str(e)}
    return asyncio.run(_do())


def main():
    p = argparse.ArgumentParser(description="一键退出全部群组 (随机延时)")
    p.add_argument("account_ids", nargs="*", type=int, help="账号ID")
    p.add_argument("--min", type=float, default=0.3, help="群组间最小延时(秒)")
    p.add_argument("--max", type=float, default=1.5, help="群组间最大延时(秒)")
    p.add_argument("--account-min", type=float, default=0.8, help="账号间最小延时(秒)")
    p.add_argument("--account-max", type=float, default=3.5, help="账号间最大延时(秒)")
    p.add_argument("--db", default="data/tg777.db")
    args = p.parse_args()

    db = Database(args.db)
    accounts = db.list_accounts()
    if not accounts: print("无账号"); return
    if args.account_ids: accounts = [a for a in accounts if a["id"] in args.account_ids]

    print(f"一键退出群组: {len(accounts)}个账号 | 群内延时:{args.min}~{args.max}s | 账号间:{args.account_min}~{args.account_max}s\n")

    total = 0
    for i, acc in enumerate(accounts):
        if i > 0:
            d = human_delay(args.account_min, args.account_max)
            print(f"  ⏱ 账号间等待 {d:.1f}s ...")
            time.sleep(d)

        sp = acc["session_path"]
        if not os.path.isfile(sp): print(f"  [{acc['id']}] ❌ session"); continue
        print(f"  [{acc['id']}] {acc['phone']} ... ", end="", flush=True)
        r = leave_all(sp, acc["phone"], acc.get("twofa_password",""), args.min, args.max)
        if r["success"]:
            print(f"✅ 退出 {r['count']} 个: {', '.join(r['groups_left'])}")
            total += r["count"]
        else: print(f"❌ {r.get('error','')[:60]}")

    print(f"\n总计: {total} 个群组")


if __name__ == "__main__":
    main()
