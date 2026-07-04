# tg777 - Telegram 账号云控操作工具

基于 Telethon (MTProto API) 的 Telegram 账号批量管理工具。
直接操作 Telegram 服务器，无需 Desktop。

## 操作映射表

| 操作 | 文件 | 命令 | 说明 |
|------|------|------|------|
| **导入账号** | `01_import_accounts.py` | `python main.py import <zip>` | 从 ZIP 批量导入 tdata/session 账号 |
| **修改 2FA** | `02_change_2fa.py` | `python main.py 2fa <旧> <新> [ids]` | 批量修改两步验证密码 |
| **修改名字** | `03_change_name.py` | `python main.py name <名字> [ids]` | 批量改 First Name / Last Name |
| **修改头像** | `04_change_avatar.py` | `python main.py avatar <图片> [ids]` | 批量更换头像 |
| **批量进群** | `05_batch_join.py` | `python main.py join <链接> [ids]` | 通过链接批量加入群组 (带延时) |
| **退出群组** | `06_batch_leave.py` | `python main.py leave [ids]` | 一键退出账号的全部群组 |

## 项目结构

```
tg777/
├── main.py                     # 统一入口
├── 01_import_accounts.py       # 操作1: ZIP导入账号
├── 02_change_2fa.py            # 操作2: 修改2FA密码
├── 03_change_name.py           # 操作3: 修改显示名字
├── 04_change_avatar.py         # 操作4: 修改头像
├── 05_batch_join.py            # 操作5: 批量链接进群
├── 06_batch_leave.py           # 操作6: 一键退出全部群组
├── README.md                   # 本文档
├── requirements.txt            # Python 依赖
├── lib/
│   ├── database.py             # SQLite 数据库操作
│   └── telethon_helper.py      # Telethon 连接辅助
└── data/
    ├── sessions/                # .session 文件存放
    ├── uploads/                 # 上传缓存
    └── tg777.db                 # 账号数据库
```

## 快速开始

```bash
# 安装
pip install -r requirements.txt

# 导入账号
python main.py import accounts.zip

# 查看已导入
python main.py list

# 查看真实名字
python main.py show

# 改 2FA
python main.py 2fa 旧密码 新密码

# 改名字 (指定账号)
python main.py name "Zhang Ning" 9 11
python main.py name "Mary" --last "" 10

# 改头像
python main.py avatar photo.jpg 9 10 11
```

## 实际操作记录 (2026-07-04)

### 账号信息

| ID | 手机 | 原名 | 新名 | 2FA |
|----|------|------|------|-----|
| 9 | +1 443-898-4638 | Fernand Simone | Zhang Ning | 0369→112211 |
| 10 | +1 660-596-4491 | Aspen Doug | Mary | 0369→112211 |
| 11 | +1 708-492-8543 | Enzo Bethan | Zhang Ning | 0369→112211 |

### 操作日志

```
1. 导入 ZIP
   python main.py import "+1 美国加拿大混合.zip"
   → 导入 3 个账号: [9] [10] [11]

2. 修改 2FA
   python main.py 2fa 0369 112211 9 10 11
   → 3/3 成功

3. 查询名字
   python main.py show
   → [9] Fernand Simone
   → [10] Aspen Doug
   → [11] Enzo Bethan

4. 修改名字
   python main.py name "Zhang Ning" --last "" 9 11
   → [9] Fernand → Zhang Ning ✅
   → [11] Enzo → Zhang Ning ✅

   python main.py name "Mary" --last "" 10
   → [10] Aspen → Mary ✅

6. 批量进群 (带延时)
   python main.py join "https://t.me/+t2D7VX2fkB4xNThh" 9 10 11 --delay 0.5
   → 9→0.5s→10→0.5s→11, 全部加入 ✅

7. 一键退出全部群组
   python main.py leave 9 10 11
   → 9: 宝宝巴士✅ 测试✅ | 10: 宝宝巴士✅ 测试✅ | 11: 宝宝巴士✅ 测试✅
   → 总计退出 6 个群组

5. 修改头像
   python main.py avatar photo1.jpg 9
   → [9] 头像已更换 ✅

   python main.py avatar photo2.jpg 10 11
   → [10] [11] 头像已更换 ✅
```

## 技术说明

- **引擎**: Telethon (MTProto API)，非 Telegram Desktop
- **API**: 使用 Telegram 默认 API ID/Hash (可通过 --api-id 自定义)
- **数据库**: SQLite，存储账号信息和操作记录
- **2FA**: 通过 Telethon `edit_2fa()` 修改，需提供旧密码
- **名字**: 通过 `UpdateProfileRequest` 修改 first_name/last_name
- **头像**: 通过 `UploadProfilePhotoRequest` 上传并设为头像

## 为什么不用 Telegram Desktop

在 1CPU / 1GB RAM VPS 上测试发现:
- Telegram Desktop (3.6.1) 无法创建 X11 窗口
- xdotool 键盘模拟无法命中 UI 元素
- 进程存在但不渲染任何窗口

因此改用 Telethon 直接调用 MTProto API，
更快、更可靠、更省资源。
