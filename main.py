#!/usr/bin/env python3
"""
tg777 - Telegram 账号云控操作工具
==================================
统一入口，支持所有账号操作。

用法:
    python main.py import <zip文件>
    python main.py 2fa <旧密码> <新密码> [账号ID...]
    python main.py name <新名字> [账号ID...]
    python main.py avatar <图片文件> [账号ID...]
    python main.py join <链接> [账号ID...] [--delay 0.5]
    python main.py leave [账号ID...] [--delay 0.3]
    python main.py list
    python main.py show
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def usage():
    print(__doc__)
    print("命令说明:")
    print("  import <zip>          导入 ZIP 账号包")
    print("  2fa <old> <new> [ids] 修改 2FA 密码")
    print("  name <first> [ids]    修改名字 (--last <姓>)")
    print("  avatar <img> [ids]    修改头像")
    print("  join <link> [ids]     批量进群 (--delay 秒)")
    print("  leave [ids]           一键退出全部群组 (--delay 秒)")
    print("  list                  列出所有账号")
    print("  show                  显示当前真实名字")
    print("\n示例:")
    print("  python main.py import accounts.zip")
    print("  python main.py 2fa 0369 112211 9 10 11")
    print("  python main.py name ZhangNing 9 11")
    print("  python main.py avatar photo.jpg 10")
    print("  python main.py join https://t.me/+hash 9 10 11 --delay 0.5")
    print("  python main.py leave 9 10 11")


def main():
    if len(sys.argv) < 2:
        usage()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "import":
        from _01_import_accounts import import_zip
        if not args:
            print("用法: python main.py import <zip文件>")
            return
        import_zip(args[0])

    elif cmd == "2fa":
        if len(args) < 2:
            print("用法: python main.py 2fa <旧密码> <新密码> [ids]")
            return
        import _02_change_2fa as m
        # 重新构造 argparse 参数
        sys.argv = ["02"] + args
        m.main()

    elif cmd == "name":
        if not args:
            print("用法: python main.py name <新名字> [ids]")
            return
        import _03_change_name as m
        sys.argv = ["03"] + args
        m.main()

    elif cmd == "avatar":
        if not args:
            print("用法: python main.py avatar <图片> [ids]")
            return
        import _04_change_avatar as m
        sys.argv = ["04"] + args
        m.main()

    elif cmd == "join":
        if not args:
            print("用法: python main.py join <链接> [ids] [--delay 0.5]")
            return
        import _05_batch_join as m
        sys.argv = ["05"] + args
        m.main()

    elif cmd == "leave":
        import _06_batch_leave as m
        sys.argv = ["06"] + args
        m.main()

    elif cmd == "list":
        from lib.database import Database
        db = Database()
        for acc in db.list_accounts():
            print(f"  [{acc['id']}] {acc['phone']} | {acc['name']} | 2fa={'有' if acc['twofa_password'] else '无'}")

    elif cmd == "show":
        from _03_change_name import get_current_names
        get_current_names("data/tg777.db")

    else:
        print(f"未知命令: {cmd}")
        usage()


if __name__ == "__main__":
    main()
