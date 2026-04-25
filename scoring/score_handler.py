"""
score_handler.py — 接收用户评分命令，记录 gold / negative 样本

支持的命令（由 CLAUDE.md 里的主 agent 解析后调用）：
  /5 <消息编号 或 '上一条'>    # 5星，写入 gold.jsonl
  /1 <消息编号 或 '上一条'>    # 1星，写入 negative.jsonl
  /good, /bad, /👍, /👎 同义

每条 gold 记录：
{
  "id": "score_<uuid>",
  "timestamp": "2026-...",
  "user_input": "...",         # 你当时发的
  "sylvia_reply": "...",       # Sylvia 的回复
  "score": 5 | 1,
  "retrieval_hits": [...],     # 这条回复当时检索到的 top-K
  "context": [...]             # 前几轮
}
"""

import sys
import io
import json
import argparse
import uuid
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCORING_DIR = Path(r"D:\sylvia_skill\scoring")
SCORING_DIR.mkdir(exist_ok=True)
GOLD = SCORING_DIR / "gold.jsonl"
NEG = SCORING_DIR / "negative.jsonl"
RECENT_REPLY_BUFFER = Path(r"D:\sylvia_skill\memory\recent_replies.jsonl")


def add_record(is_positive: bool, record: dict):
    target = GOLD if is_positive else NEG
    record["id"] = f"score_{uuid.uuid4().hex[:12]}"
    record["timestamp"] = datetime.now().isoformat()
    record["score"] = 5 if is_positive else 1
    with open(target, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record["id"]


def load_recent_reply(which: str = "last"):
    """从 recent_replies.jsonl 取指定的对话记录

    which = 'last' 取最后一条
    which = '<数字>' 取倒数第 N 条
    """
    if not RECENT_REPLY_BUFFER.exists():
        return None
    lines = RECENT_REPLY_BUFFER.read_text(encoding="utf-8").strip().split("\n")
    lines = [l for l in lines if l]
    if not lines:
        return None
    if which == "last":
        return json.loads(lines[-1])
    try:
        n = int(which)
        if n > len(lines):
            return None
        return json.loads(lines[-n])
    except ValueError:
        return None


def save_recent_reply(record: dict):
    """CLAUDE agent 每次回复后调用此函数入 buffer"""
    RECENT_REPLY_BUFFER.parent.mkdir(exist_ok=True)
    with open(RECENT_REPLY_BUFFER, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p_score = sub.add_parser("score", help="打分")
    p_score.add_argument("value", choices=["5", "1", "good", "bad"])
    p_score.add_argument("target", default="last", nargs="?")
    sub.add_parser("stats", help="看 gold/negative 累积数")
    sub.add_parser("export", help="导出 gold 作为 few-shot 样本")

    args = parser.parse_args()

    if args.cmd == "score":
        record = load_recent_reply(args.target)
        if not record:
            print("没找到目标回复，不动作")
            return
        is_pos = args.value in ("5", "good")
        rid = add_record(is_pos, record)
        print(f"{'金标准 gold' if is_pos else '反例 negative'} · 记为 {rid}")

    elif args.cmd == "stats":
        gold_n = sum(1 for _ in open(GOLD, encoding="utf-8")) if GOLD.exists() else 0
        neg_n = sum(1 for _ in open(NEG, encoding="utf-8")) if NEG.exists() else 0
        print(f"Gold（5星）: {gold_n} 条")
        print(f"Negative（1星）: {neg_n} 条")

    elif args.cmd == "export":
        # 导出 gold.jsonl 的样本作为 few-shot 放到 retrieval 时额外注入
        if GOLD.exists():
            out = SCORING_DIR / "gold_fewshot.json"
            data = []
            with open(GOLD, encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    data.append({
                        "input": r.get("user_input", ""),
                        "output": r.get("sylvia_reply", ""),
                        "context": r.get("context", []),
                    })
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"导出 {len(data)} 条 gold 样本到 {out}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
