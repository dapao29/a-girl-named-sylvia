"""
Sylvia 入站消息 RAG 注入 hook

Claude Code hook 接到 cc-weixin 的入站消息事件后调用：
1. 取最新用户消息 + 最近 5 轮上下文
2. 调用 RAG retrieve 拿 top-5 历史相似对话
3. 把检索结果作为额外上下文写到 short_term.json，下一轮 Claude 自动加载

输入：stdin 是 hook 事件 JSON（payload.message.text 是用户文本）
输出：stdout 写注入文本（也可以 echo 给 Claude）
"""
import sys
import io
import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

SHORT_TERM = Path(r"D:\sylvia_skill\memory\short_term.json")
RECENT_REPLIES = Path(r"D:\sylvia_skill\memory\recent_replies.jsonl")
RETRIEVE_SCRIPT = Path(r"D:\sylvia_skill\rag\retrieve.py")
PYTHON = r"C:\Users\zzh19\AppData\Local\Microsoft\WindowsApps\python3.exe"


def load_recent_context(n=5):
    """读取 short_term 里最近 N 轮"""
    if not SHORT_TERM.exists():
        return []
    try:
        data = json.loads(SHORT_TERM.read_text(encoding="utf-8"))
        return data.get("conversation_buffer", [])[-n:]
    except Exception:
        return []


def update_short_term(user_msg: str, retrieval_hits: list):
    """记当前用户消息 + 检索结果到 short_term"""
    if not SHORT_TERM.exists():
        return
    try:
        data = json.loads(SHORT_TERM.read_text(encoding="utf-8"))
    except Exception:
        return

    data["last_user_message"] = user_msg
    data.setdefault("conversation_buffer", [])
    data["conversation_buffer"].append({
        "ts": datetime.now().isoformat(),
        "speaker": "你",
        "text": user_msg,
    })
    data["conversation_buffer"] = data["conversation_buffer"][-20:]
    data["latest_retrieval_hits"] = retrieval_hits  # 给 Claude 下一轮看

    SHORT_TERM.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def call_retrieve(query: str, k: int = 5):
    """调 retrieve.py 拿 top-K"""
    env = os.environ.copy()
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    try:
        result = subprocess.run(
            [PYTHON, str(RETRIEVE_SCRIPT), "--k", str(k), "--format", "json", query],
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=60,
        )
        if result.returncode != 0:
            return []
        return json.loads(result.stdout)
    except Exception as e:
        return []


def extract_user_message(event: dict) -> str:
    """兼容多种 hook 输入格式"""
    import re as _re

    raw = ""
    # UserPromptSubmit hook 标准格式
    if "prompt" in event:
        raw = str(event["prompt"]).strip()
    elif "payload" in event:
        msg = event.get("payload", {}).get("message", {})
        if isinstance(msg, dict) and msg.get("text"):
            raw = str(msg["text"]).strip()
    elif "content" in event:
        raw = str(event["content"]).strip()
    elif "message" in event:
        m = event["message"]
        if isinstance(m, str):
            raw = m.strip()
        elif isinstance(m, dict) and "content" in m:
            raw = str(m["content"]).strip()

    # 处理 cc-weixin 的 <channel> XML 包装
    m = _re.search(r"<channel[^>]*>\s*(.*?)\s*</channel>", raw, _re.DOTALL)
    if m:
        return m.group(1).strip()
    return raw


def main():
    # 读 hook 事件
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw else {}
    except Exception:
        event = {}

    # 调试日志（永远写）
    debug_log = Path(r"D:\sylvia_skill\logs\hook_debug.log")
    debug_log.parent.mkdir(exist_ok=True)
    with open(debug_log, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] event_keys={list(event.keys()) if event else 'empty'} raw_len={len(raw)}\n")

    user_msg = extract_user_message(event)
    if not user_msg:
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write(f"  no user message extracted, raw_first200={raw[:200]}\n")
        return

    # 拼查询：最近 4 轮 + 当前消息
    recent = load_recent_context(4)
    parts = []
    for c in recent:
        parts.append(f"{c.get('speaker','?')}: {c.get('text','')[:80]}")
    parts.append(f"你: {user_msg}")
    query = " | ".join(parts)

    # RAG 检索
    hits = call_retrieve(query, k=5)

    # 写到 short_term，下一轮 Claude 自动看到
    update_short_term(user_msg, hits)

    # 同时输出到 stdout（如果作为 prompt 注入）
    print(json.dumps({
        "rag_context": hits,
        "query_used": query,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
