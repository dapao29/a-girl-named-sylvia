"""
sample_extreme.py — 抽取两端样本：最长（吵架/认真）+ 最冷淡（冷处理）

用于 v2 人格迭代：分析这两类样本里的关键词、情绪、转换触发模式
"""

import sys
import io
import json
import re
import random
from pathlib import Path
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CORPUS_DIR = Path(r"D:\sylvia_skill\rag\corpus")
OUT_DIR = Path(r"D:\sylvia_skill\persona\samples")
OUT_DIR.mkdir(exist_ok=True)


def load_wx():
    items = []
    p = CORPUS_DIR / "wx_corpus.jsonl"
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def write_jsonl(path, items):
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def main():
    print("[加载] wx_corpus...")
    items = load_wx()
    print(f"  共 {len(items):,} 条")

    # ===== 1. 最长 200 条（通常是吵架/认真复盘）=====
    long_msgs = sorted(items, key=lambda x: len(x["sylvia_reply"]), reverse=True)[:200]
    write_jsonl(OUT_DIR / "longest_200.jsonl", long_msgs)
    print(f"\n[最长 200] 长度 {len(long_msgs[0]['sylvia_reply'])} → {len(long_msgs[-1]['sylvia_reply'])}")
    print("Top 5 最长消息（首 200 字）:")
    for i, it in enumerate(long_msgs[:5], 1):
        snippet = it["sylvia_reply"][:200].replace("\n", " ")
        print(f"  {i}. ({len(it['sylvia_reply'])}字, {it['timestamp'][:10]}) {snippet}")

    # ===== 2. 最冷淡：1-3 字回复，且上下文有"情感波动"信号 =====
    cold_indicators = re.compile(r"[?？！!]|睡|分手|不理|生气|算了|哥|宝|对不起|不开心|拜拜")
    cold_replies = re.compile(r"^(嗯|哦|好|行|是|对|没|不|？|没事|算了|滚|走|去吧)$")

    cold_samples = []
    for it in items:
        reply = it["sylvia_reply"].strip()
        if not cold_replies.match(reply):
            continue
        # 检查上下文是否有情感波动信号
        ctx = " ".join(c.get("text", "") for c in it["context"])
        if cold_indicators.search(ctx):
            cold_samples.append(it)
    cold_samples = cold_samples[:300]
    write_jsonl(OUT_DIR / "cold_300.jsonl", cold_samples)
    print(f"\n[冷处理] {len(cold_samples)} 条")

    # ===== 3. 高情绪密度的短消息（"sb" "滚" "[发怒]" 等）=====
    angry_pat = re.compile(r"sb|滚|分手|无所谓|累了|拉黑|不说了|\[发怒\]|\?{2,}")
    angry_msgs = [it for it in items if angry_pat.search(it["sylvia_reply"])][:200]
    write_jsonl(OUT_DIR / "angry_200.jsonl", angry_msgs)
    print(f"\n[爆发] {len(angry_msgs)} 条")

    # ===== 4. 撒娇/亲昵 =====
    sweet_pat = re.compile(r"宝宝|宝狗|笨狗|小狗|想你|好喜欢|抱抱|人家|猪猪")
    sweet_msgs = [it for it in items if sweet_pat.search(it["sylvia_reply"])][:200]
    write_jsonl(OUT_DIR / "sweet_200.jsonl", sweet_msgs)
    print(f"\n[亲昵] {len(sweet_msgs)} 条")

    # ===== 5. 标志性表情用法 =====
    emoji_contexts = {
        "[发怒]": [], "[破涕为笑]": [], "[汗]": [], "[强]": [], "[合十]": [], "[玫瑰]": []
    }
    for it in items:
        for em in emoji_contexts:
            if em in it["sylvia_reply"]:
                if len(emoji_contexts[em]) < 50:
                    emoji_contexts[em].append({
                        "context": [c["text"] for c in it["context"]],
                        "reply": it["sylvia_reply"],
                    })
    with open(OUT_DIR / "emoji_contexts.json", "w", encoding="utf-8") as f:
        json.dump(emoji_contexts, f, ensure_ascii=False, indent=2)
    for em, samples in emoji_contexts.items():
        print(f"[{em}] {len(samples)} 条")

    print(f"\n[完成] 输出到 {OUT_DIR}")


if __name__ == "__main__":
    main()
