"""
build_index.py — 用 BGE-small-zh 嵌入所有语料，建 FAISS 索引

输出：
  vector_db/index.bin     — FAISS HNSW/Flat 索引
  vector_db/metadata.jsonl — 每条 metadata 按 id 顺序

用法：
  python build_index.py          # 全量
  python build_index.py --test 100  # 只跑前 100 条
"""

import sys
import io
import json
import argparse
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CORPUS_DIR = Path(r"D:\sylvia_skill\rag\corpus")
INDEX_DIR = Path(r"D:\sylvia_skill\rag\vector_db")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
EMBED_DIM = 512
BATCH_SIZE = 32


def load_corpus():
    items = []
    for f in CORPUS_DIR.glob("*.jsonl"):
        with open(f, "r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                items.append(json.loads(line))
    return items


def context_to_query_text(context: list) -> str:
    return " | ".join(f"{c['speaker']}: {c['text']}" for c in context)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=int, default=0)
    args = parser.parse_args()

    print("[加载] corpus...")
    items = load_corpus()
    if args.test:
        items = items[:args.test]
    print(f"[语料] 共 {len(items):,} 条")

    print(f"[模型] 加载 {MODEL_NAME} ...")
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import faiss
    model = SentenceTransformer(MODEL_NAME, device="cpu")

    # 创建 FAISS 索引（Flat IP，归一化向量 = cosine sim）
    print(f"[FAISS] 初始化 IndexFlatIP dim={EMBED_DIM}")
    index = faiss.IndexFlatIP(EMBED_DIM)

    metadata_file = INDEX_DIR / "metadata.jsonl"
    metadata_fp = open(metadata_file, "w", encoding="utf-8")

    print(f"[索引] 开始嵌入（每批 {BATCH_SIZE}）...")
    t0 = time.time()
    total = len(items)

    all_embeddings = []
    for i in range(0, total, BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        texts = [context_to_query_text(it["context"]) for it in batch]

        embeddings = model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True,
            show_progress_bar=False
        ).astype(np.float32)
        index.add(embeddings)

        # 写 metadata
        for it in batch:
            md = {
                "id": it["id"],
                "sylvia_reply": it["sylvia_reply"][:1500],
                "timestamp": str(it.get("timestamp", "")),
                "source": it.get("source", ""),
                "context_last3": it["context"][-3:],
            }
            metadata_fp.write(json.dumps(md, ensure_ascii=False) + "\n")

        done = min(i + BATCH_SIZE, total)
        elapsed = time.time() - t0
        rate = done / elapsed if elapsed > 0 else 0
        eta_min = (total - done) / rate / 60 if rate > 0 else 0
        if done % (BATCH_SIZE * 10) == 0 or done == total:
            print(f"  [{done:,}/{total:,}] {rate:.1f}/s, ETA {eta_min:.1f}min")

        # 每 10K 条 flush 一次防止意外
        if done % 10000 == 0:
            metadata_fp.flush()
            faiss.write_index(index, str(INDEX_DIR / "index.bin"))

    metadata_fp.close()
    faiss.write_index(index, str(INDEX_DIR / "index.bin"))

    elapsed = time.time() - t0
    print(f"\n[完成] {total:,} 条 · 耗时 {elapsed/60:.1f} 分钟")
    print(f"[索引] {INDEX_DIR / 'index.bin'} · ntotal={index.ntotal}")
    print(f"[元数据] {metadata_file}")


if __name__ == "__main__":
    main()
