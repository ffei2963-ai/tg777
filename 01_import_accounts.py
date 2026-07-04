#!/usr/bin/env python3
"""
操作 1: ZIP 导入账号
=====================
从 Telegram 导出的 ZIP 文件批量导入账号。
ZIP 内每个子目录 = 一个独立账号，
包含 tdata 文件夹、.session 文件、info.json、2fa.txt 等。

用法:
    python 01_import_accounts.py <zip_path> [--db data/tg777.db]

示例:
    python 01_import_accounts.py accounts.zip
    python 01_import_accounts.py my_export.zip --db my.db
"""

import os
import sys
import json
import uuid
import argparse
import zipfile
import shutil
import re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.database import Database

SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sessions")


def detect_account(folder_path: str) -> dict:
    """检测文件夹中的账号文件结构"""
    info = {
        "has_tdata": False, "has_session": False, "has_json": False,
        "has_twofa": False, "phone": "", "name": os.path.basename(folder_path),
        "tdata_path": "", "session_file": "", "twofa_password": "",
    }
    if not os.path.isdir(folder_path):
        return info
    for item in os.listdir(folder_path):
        ip = os.path.join(folder_path, item)
        if item == "tdata" and os.path.isdir(ip):
            info["has_tdata"] = True
            info["tdata_path"] = ip
        elif item.endswith(".session") and not item.endswith(".session-journal"):
            info["has_session"] = True
            info["session_file"] = ip
        elif item.endswith(".json"):
            info["has_json"] = True
            try:
                with open(ip, "r", encoding="utf-8") as f:
                    d = json.load(f)
                info["phone"] = d.get("phone", "")
                info["name"] = d.get("name", info["name"])
            except Exception:
                pass
        elif item.endswith(".txt") and "2fa" in item.lower():
            info["has_twofa"] = True
            try:
                with open(ip, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            info["twofa_password"] = line
                            break
            except Exception:
                pass
    if not info["phone"]:
        m = re.findall(r'\+?\d{7,15}', info["name"])
        if m:
            info["phone"] = m[0]
    return info


def import_zip(zip_path: str, db_path: str = "data/tg777.db") -> list[dict]:
    db = Database(db_path)
    if not os.path.isfile(zip_path):
        print(f"错误: 找不到文件 {zip_path}")
        return []

    extract_dir = Path.home() / ".tg777_extract"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    os.makedirs(str(extract_dir))

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(str(extract_dir))
    print(f"ZIP 解压完成: {zip_path}")

    items = sorted(os.listdir(str(extract_dir)))
    subdirs = [d for d in items if os.path.isdir(extract_dir / d)]

    if not subdirs:
        subdirs = ["."]
        os.chdir(str(extract_dir))

    results = []
    for subdir in subdirs:
        folder = str(extract_dir / subdir) if subdir != "." else str(extract_dir)
        info = detect_account(folder)

        phone = info["phone"]
        if phone and db.list_accounts():
            existing = [a for a in db.list_accounts() if a["phone"] == phone]
            if existing:
                print(f"  跳过: {info['name']} ({phone}) - 已存在")
                results.append({"name": info["name"], "phone": phone, "skipped": True})
                continue

        # 处理 session 文件
        if info["has_session"]:
            dest = os.path.join(SESSIONS_DIR, f"{uuid.uuid4().hex[:12]}.session")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(info["session_file"], dest)
        else:
            dest = os.path.join(SESSIONS_DIR, f"pending_{uuid.uuid4().hex[:8]}.tdata_only")

        aid = db.add_account(
            name=info["name"], phone=phone, session_path=dest,
            twofa_password=info["twofa_password"],
            metadata={"tdata": info["has_tdata"], "source": folder}
        )
        print(f"  已导入: [{aid}] {info['name']} | {phone} | session={'✅' if info['has_session'] else '⚠️tdata'} | 2fa={'✅' if info['twofa_password'] else '❌'}")
        results.append({"account_id": aid, "name": info["name"], "phone": phone,
                        "has_session": info["has_session"], "twofa": bool(info["twofa_password"])})

    shutil.rmtree(str(extract_dir), ignore_errors=True)
    print(f"\n导入完成: {len([r for r in results if not r.get('skipped')])} 个新账号, "
          f"跳过 {len([r for r in results if r.get('skipped')])} 个重复")
    return results


def main():
    parser = argparse.ArgumentParser(description="ZIP 导入 Telegram 账号")
    parser.add_argument("zip_path", help="账号 ZIP 文件路径")
    parser.add_argument("--db", default="data/tg777.db", help="数据库路径")
    args = parser.parse_args()
    import_zip(args.zip_path, args.db)


if __name__ == "__main__":
    main()
