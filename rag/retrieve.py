"""
retrieve.py — 给定 query，返回 top-K 最相似的 Sylvia 历史对话

用法：
  python retrieve.py "你今天在干啥 | Sylvia: 没干啥"
  python retrieve.py --k 5 "在干啥"
"""

import sys
import io
import json
import argparse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

INDEX_DIR = Path(r"D:\sylvia_skill\rag\vector_db")
MODEL_NAME = "BAAI/bge-small-zh-v1.5"

_cached = {}


def get_resources():
    if _cached:
        return _cached["model"], _cached["index"], _cached["metas"]
    from sentence_transformers import SentenceTransformer
    import faiss
    print("[加载] 模型 + 索引...", file=sys.stderr)
    model = SentenceTransformer(MODEL_NAME, device="cpu")
    index = faiss.read_index(str(INDEX_DIR / "index.bin"))
    metas = []
    with open(INDEX_DIR / "metadata.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            metas.append(json.loads(line))
    _cached["model"] = model
    _cached["index"] = index
    _cached["metas"] = metas
    return model, index, metas


def retrieve(query: str, k: int = 10, source_filter: str = None):
    import numpy as np
    model, index, metas = get_resources()
    emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
    k_search = k * 5 if source_filter else k  # 过滤需求查更多
    D, I = index.search(emb, min(k_search, index.ntotal))
    results = []
    for sim, idx in zip(D[0], I[0]):
        if idx < 0 or idx >= len(metas):
            continue
        m = metas[idx]
        if source_filter and m.get("source") != source_filter:
            continue
        results.append({
            "id": m["id"],
            "similarity": float(sim),
            "sylvia_reply": m["sylvia_reply"],
            "timestamp": m["timestamp"],
            "source": m["source"],
            "context_last3": m["context_last3"],
        })
        if len(results) >= k:
            break
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--source", choices=["wx", "call"], default=None)
    parser.add_argument("--format", choices=["json", "pretty"], default="pretty")
    args = parser.parse_args()

    hits = retrieve(args.query, k=args.k, source_filter=args.source)
    if args.format == "json":
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    else:
        for i, h in enumerate(hits, 1):
            print(f"\n━━━━ {i} · sim={h['similarity']:.3f} · {h['source']} · {h['timestamp']} ━━━━")
            for c in h["context_last3"]:
                print(f"  {c['speaker']}: {c['text'][:80]}")
            print(f"💬 Sylvia: {h['sylvia_reply']}")


if __name__ == "__main__":
    main()
