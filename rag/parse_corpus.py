"""
parse_corpus.py — 解析微信 Excel + 通话 JSON，输出 RAG 索引就绪的 JSONL

输出格式（每行一条 Sylvia 的回复 + 前 N 轮上下文）：
{
  "id": "wx_123456",
  "timestamp": "2022-07-15 23:42:11",
  "context": [
      {"speaker": "你", "text": "..."},
      {"speaker": "Sylvia", "text": "..."},
      {"speaker": "你", "text": "..."}   # 最后一条通常是你
  ],
  "sylvia_reply": "...",     # 这是我们要预测/模仿的
  "source": "wx" | "call"
}

用法：
  python parse_corpus.py all    # 解析全部（wx + call）
  python parse_corpus.py wx     # 只解析微信
  python parse_corpus.py call   # 只解析通话
"""

import sys
import io
import json
import os
import re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

EXCEL_PATH = r"F:\texts\私聊_Sylvia.xlsx"          # 改成你导出的微信 Excel 路径
CALL_JSON_DIR = r"D:\path\to\call_transcripts\json"  # 改成你的通话转写 JSON 目录
OUTPUT_DIR = Path(r"D:\sylvia_skill\rag\corpus")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYLVIA_ALIASES = {"Sylvia🍬", "Sylvia"}  # 改成她在你导出文件里的所有称呼（昵称、备注名、本名）
CONTEXT_N = 5  # 保留前 N 轮上下文


def parse_excel():
    """解析微信 Excel"""
    import pandas as pd
    print(f"[解析] 读取 {EXCEL_PATH} ...")
    df = pd.read_excel(EXCEL_PATH, skiprows=4, header=None,
                       names=["序号", "时间", "发送者", "类型", "内容"])
    df = df.dropna(subset=["内容"])
    df = df[df["类型"] == "文本消息"]  # 只要文本
    df["内容"] = df["内容"].astype(str).str.strip()
    df = df[df["内容"].str.len() > 0]
    df = df[df["内容"].str.len() < 2000]  # 过滤超长（通常是转发/系统消息）
    print(f"[解析] 有效文本消息 {len(df):,} 条")

    # 按时间排序，然后滑窗生成 (context, sylvia_reply)
    df = df.sort_values("时间").reset_index(drop=True)

    items = []
    messages = df[["时间", "发送者", "内容"]].values.tolist()

    for i, (ts, speaker, text) in enumerate(messages):
        if speaker not in SYLVIA_ALIASES:
            continue
        # 找前 N 轮（包含 speaker 变化的对话往复）
        context = []
        j = i - 1
        while j >= 0 and len(context) < CONTEXT_N:
            prev_ts, prev_speaker, prev_text = messages[j]
            context.insert(0, {
                "speaker": "Sylvia" if prev_speaker in SYLVIA_ALIASES else "你",
                "text": prev_text,
            })
            j -= 1
        if not context:
            continue  # 第一条消息没有上下文
        items.append({
            "id": f"wx_{i:07d}",
            "timestamp": str(ts),
            "context": context,
            "sylvia_reply": text,
            "source": "wx",
        })

    out = OUTPUT_DIR / "wx_corpus.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"[写入] {out} · {len(items):,} 条 Sylvia 回复")
    return len(items)


def parse_calls():
    """解析通话 JSON — 每个 chunk 是 Sylvia 说的一段话（单边录音）"""
    files = list(Path(CALL_JSON_DIR).glob("*.json"))
    print(f"[解析] 通话 JSON 文件 {len(files)} 个")
    items = []
    empty_filter = re.compile(r"^[。\s.\,]+$")  # 纯句号/空白

    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            chunks = data.get("chunks", [])
            call_id = fpath.stem

            for idx, chunk in enumerate(chunks):
                text = (chunk.get("text") or "").strip()
                # 过滤太短/纯句号的无信息段
                if len(text) < 5 or empty_filter.match(text):
                    continue
                # 合并开头的 . 序列
                text = re.sub(r"^[。\.\s]{3,}", "", text).strip()
                if len(text) < 5:
                    continue
                # 上下文：同一通话的前 N 个 chunk
                context = []
                j = idx - 1
                while j >= 0 and len(context) < CONTEXT_N:
                    prev_text = (chunks[j].get("text") or "").strip()
                    if len(prev_text) >= 5 and not empty_filter.match(prev_text):
                        context.insert(0, {
                            "speaker": "Sylvia",  # 通话全是她
                            "text": prev_text,
                        })
                    j -= 1
                items.append({
                    "id": f"call_{call_id}_{idx:03d}",
                    "timestamp": data.get("created_at", ""),
                    "context": context,
                    "sylvia_reply": text,
                    "source": "call",
                    "call_id": call_id,
                    "start_sec": chunk.get("start_sec"),
                    "end_sec": chunk.get("end_sec"),
                })
        except Exception as e:
            print(f"[跳过] {fpath.name}: {e}")

    out = OUTPUT_DIR / "call_corpus.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"[写入] {out} · {len(items):,} 条通话片段")
    return len(items)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    total = 0
    if mode in ("all", "wx"):
        total += parse_excel()
    if mode in ("all", "call"):
        total += parse_calls()
    print(f"\n[完成] 共 {total:,} 条语料")


if __name__ == "__main__":
    main()
