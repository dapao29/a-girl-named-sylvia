"""
persona_iterate.py — 分批提炼人格画像，多版本演进

流程：
1. v1_base.md — 从 corpus 前 10K 条消息提炼基础人格（已有现成的 persona.md 即可作为 v1）
2. v2_refined.md — 加入 10K-30K 条的特征，对比 v1 追加新规则
3. v3_...md — 20K-50K
4. v4_...md — 50K-100K
5. v5_latest.md — 100K+ 及通话补充

每次迭代输出一份 diff 到 change_log.md，说明新增了哪些规则。

用法：
  python persona_iterate.py stats            # 看语料基础统计
  python persona_iterate.py batch 10000 30000  # 提炼某一段的特征
  python persona_iterate.py diff v1 v2       # 对比两版差异
"""

import sys
import io
import json
import re
import argparse
from pathlib import Path
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CORPUS_DIR = Path(r"D:\sylvia_skill\rag\corpus")
PERSONA_DIR = Path(r"D:\sylvia_skill\persona")
PERSONA_DIR.mkdir(exist_ok=True)


def load_all_replies():
    """加载全部 Sylvia 的回复"""
    replies = []
    for f in CORPUS_DIR.glob("*.jsonl"):
        with open(f, "r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                it = json.loads(line)
                replies.append({
                    "text": it["sylvia_reply"],
                    "timestamp": it.get("timestamp", ""),
                    "source": it.get("source", ""),
                })
    return replies


def batch_stats(replies, start, end):
    """对一段 replies 做统计：长度分布、高频词、情绪标记等"""
    batch = replies[start:end]
    print(f"\n=== 批次 {start}-{end} · {len(batch)} 条 ===")

    # 长度分布
    lengths = [len(r["text"]) for r in batch]
    if lengths:
        lengths.sort()
        mid = lengths[len(lengths) // 2]
        print(f"消息长度：中位数 {mid}，平均 {sum(lengths)/len(lengths):.1f}，最长 {max(lengths)}")

    # 高频口头禅
    word_counter = Counter()
    for r in batch:
        t = r["text"]
        # 常见口头禅的简单匹配
        phrases = re.findall(r"俺|为啥|咋|啥|中|好德|好好好|笑死|啊这|哈哈+|害|\.{3,}|\?+", t)
        word_counter.update(phrases)

    print("高频口头禅 TOP 15:")
    for w, c in word_counter.most_common(15):
        print(f"  {w}: {c}")

    # 情绪标记
    emotions = {
        "生气": re.compile(r"\?{2,}|滚|分手|无所谓|累了|sb"),
        "开心/撒娇": re.compile(r"宝宝|狗狗|笑死|哈哈|666|NB|\[强\]|\[玫瑰\]"),
        "冷处理": re.compile(r"^(哦|好|行|嗯)$"),
        "撒娇求关注": re.compile(r"人家|抱抱"),
    }
    emotion_counter = Counter()
    for r in batch:
        for name, pat in emotions.items():
            if pat.search(r["text"]):
                emotion_counter[name] += 1

    print("情绪标记分布:")
    for name, c in emotion_counter.most_common():
        print(f"  {name}: {c} ({c*100/len(batch):.1f}%)")

    return {
        "batch_size": len(batch),
        "median_length": lengths[len(lengths)//2] if lengths else 0,
        "top_phrases": dict(word_counter.most_common(30)),
        "emotion_distribution": dict(emotion_counter),
    }


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    p_stats = sub.add_parser("stats", help="总统计")
    p_batch = sub.add_parser("batch", help="分段统计")
    p_batch.add_argument("start", type=int)
    p_batch.add_argument("end", type=int)
    p_diff = sub.add_parser("diff", help="对比两版人格")
    p_diff.add_argument("v1")
    p_diff.add_argument("v2")

    args = parser.parse_args()

    if args.cmd == "stats":
        replies = load_all_replies()
        print(f"总 Sylvia 回复数：{len(replies):,}")
        # 分 6 批分别统计
        n = len(replies)
        step = n // 6
        for i in range(6):
            batch_stats(replies, i * step, (i + 1) * step)

    elif args.cmd == "batch":
        replies = load_all_replies()
        batch_stats(replies, args.start, args.end)

    elif args.cmd == "diff":
        # TODO: 读两版 persona md 做简单 diff
        print("TODO: diff 功能待实现（手动对比也可以）")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
