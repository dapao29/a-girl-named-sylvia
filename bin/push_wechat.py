#!/usr/bin/env python3
"""
push_wechat.py — 独立的微信推送脚本（不依赖 cc-weixin MCP）

用法：
  python push_wechat.py "要发送的消息"                         # 发给默认用户
  python push_wechat.py --to <chat_id> "要发送的消息"
  echo "消息" | python push_wechat.py --stdin                  # 从 stdin 读

依赖：
  - cc-weixin 持久化的 contexts.json（Sylvia 收到消息后会写入）
  - account.json 里的 token

返回码：
  0 成功
  1 参数错误
  2 token 缺失
  3 context_token 缺失（用户从未给 bot 发过消息）
  4 API 调用失败
"""

import sys
import io
import json
import argparse
import secrets
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

DEFAULT_USER = ""  # 改成你的 wechat openid，例如 "oXXXXXXXXXXXXXXXX@im.wechat"
ACCOUNT_FILE = Path.home() / ".claude" / "channels" / "weixin" / "account.json"
CONTEXTS_FILE = Path.home() / ".claude" / "channels" / "weixin" / "contexts.json"
LOG_FILE = Path(r"D:\sylvia_skill\logs\push_wechat.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, file=sys.stderr)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_token() -> str:
    if not ACCOUNT_FILE.exists():
        log("ERROR: account.json 不存在，请先扫码登录 cc-weixin")
        sys.exit(2)
    data = json.loads(ACCOUNT_FILE.read_text(encoding="utf-8"))
    token = data.get("token")
    if not token:
        log("ERROR: account.json 里 token 为空")
        sys.exit(2)
    return token


def load_context_token(user_id: str) -> str:
    """从 cc-weixin 持久化的 contexts.json 读取 user 的 context_token"""
    if not CONTEXTS_FILE.exists():
        log(f"ERROR: {CONTEXTS_FILE} 不存在 — Sylvia 还没收到过 {user_id} 的消息")
        log("提示：你先在微信给 bot 发一条消息，cc-weixin 才会缓存 context_token")
        sys.exit(3)
    data = json.loads(CONTEXTS_FILE.read_text(encoding="utf-8"))
    ctx = data.get(user_id)
    if not ctx:
        log(f"ERROR: contexts.json 里没有 {user_id} 的 context_token")
        log("提示：你给 bot 发一条消息触发缓存")
        sys.exit(3)
    return ctx


def send(to: str, text: str, token: str, context_token: str) -> dict:
    """直接调 ilinkai API 发送"""
    body = {
        "msg": {
            "to_user_id": to,
            "from_user_id": "",
            "client_id": secrets.token_hex(16),
            "message_type": 2,    # BOT
            "message_state": 2,   # FINISH
            "context_token": context_token,
            "item_list": [{"type": 1, "text_item": {"text": text}}],
        },
        "base_info": {"channel_version": "0.1.0"},
    }
    headers = {
        "Content-Type": "application/json",
        "AuthorizationType": "ilink_bot_token",
        "Authorization": f"Bearer {token}",
        "X-WECHAT-UIN": secrets.token_urlsafe(4),
    }
    req = urllib.request.Request(
        "https://ilinkai.weixin.qq.com/ilink/bot/sendmessage",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.URLError as e:
        log(f"ERROR: API 请求失败 {e}")
        sys.exit(4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", default=DEFAULT_USER, help="目标 chat_id")
    parser.add_argument("--stdin", action="store_true", help="从 stdin 读消息")
    parser.add_argument("text", nargs="?", help="要发的消息文本")
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read().strip()
    elif args.text:
        text = args.text
    else:
        parser.error("请用参数 'text' 或 --stdin 提供消息")

    if not text:
        log("ERROR: 消息为空")
        sys.exit(1)

    token = load_token()
    ctx = load_context_token(args.to)

    log(f"send → {args.to}, {len(text)} chars")
    result = send(args.to, text, token, ctx)
    log(f"resp: {result}")

    if result.get("ret") and result["ret"] != 0:
        log(f"ERROR: API 返回 ret={result['ret']}")
        sys.exit(4)
    log("OK 发送成功")


if __name__ == "__main__":
    main()
