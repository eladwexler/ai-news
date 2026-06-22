#!/usr/bin/env python3
"""Chunk the ai-news corpus into BM25 retrieval passages (index/chunks.jsonl).

Walks every dated folder (<YYYY-MM-DD>/*.txt) of primary-source industry articles
fetched by news-today.py / all-news.py — SemiAnalysis, Fabricated Knowledge, Epoch AI,
Next Platform, Data Center Dynamics, Semiconductor Engineering, EE Times, … — parses the
`SOURCE/TITLE/DATE/URL` header, splits the body into ~220-word overlapping chunks, tags
each chunk with the four investment pillars (reusing process-news.py's keyword map), and
writes index/chunks.jsonl. Each line:
  {id, doc, title, date, url, source, pillars, text}

`source` is the publication (SemiAnalysis, Epoch_AI, …) so a reader can weight a hit by
outlet. This is the corpus behind the "Industry Brain" — the only hard-data lens in the
trading-analysis pipeline (every other brain is a personality/crowd corpus). Re-run after
each news fetch (the trading-analysis `ensure_news.py` gate does this automatically).
"""
import json, os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "index", "chunks.jsonl")
WORDS, OVERLAP = 220, 50
DATE_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GENERATED = {"human-readable.txt", "optimized_llm_payload.json", "stock-analysis.md"}

# The four investable pillars — keyword map kept in sync with process-news.py
PILLARS = {
    "macro_finance": [
        "capex", "capital expenditure", "hyperscaler", "free cash flow",
        "operating margins", "depreciation schedule",
    ],
    "silicon_hardware": [
        "gpu", "tpu", "asic", "accelerator", "hbm", "inference", "training workload",
    ],
    "supply_chain_chokepoints": [
        "advanced packaging", "cowos", "tsmc", "foundry", "yield rate", "lead time",
    ],
    "physical_infrastructure": [
        "data center", "power grid", "electricity", "transformer", "liquid cooling", "megawatt",
    ],
}


def tag_pillars(text):
    low = text.lower()
    return [p for p, kws in PILLARS.items() if any(k in low for k in kws)]


def parse_file(path):
    """Return (meta_dict, body) for an ai-news article .txt."""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    meta, body_start = {}, 0
    for i, line in enumerate(lines):
        s = line.strip()
        if set(s) == {"-"} and len(s) >= 10:  # the 40-dash separator
            body_start = i + 1
            break
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip().lower()] = v.strip()
    body = "".join(lines[body_start:]).strip()
    # drop a leading "CONTENT:" label if present
    body = re.sub(r"^CONTENT:\s*", "", body)
    return meta, body


def chunk_words(text):
    words = text.split()
    step = WORDS - OVERLAP
    for i in range(0, max(1, len(words)), step):
        seg = words[i:i + WORDS]
        if not seg:
            break
        yield " ".join(seg)
        if i + WORDS >= len(words):
            break


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    date_dirs = sorted(d for d in os.listdir(ROOT)
                       if DATE_DIR.match(d) and os.path.isdir(os.path.join(ROOT, d)))
    n_files = n_chunks = 0
    with open(OUT, "w", encoding="utf-8") as out:
        for dd in date_dirs:
            folder = os.path.join(ROOT, dd)
            for fn in sorted(os.listdir(folder)):
                if not fn.endswith(".txt") or fn in GENERATED:
                    continue
                path = os.path.join(folder, fn)
                meta, body = parse_file(path)
                if not body:
                    continue
                n_files += 1
                doc = f"{dd}/{fn}"
                source = meta.get("source", "")
                # prefer the folder date (fetch date) — stable, sortable
                date = dd
                title = meta.get("title", fn[:-4])
                url = meta.get("url", "")
                pillars = tag_pillars(body)
                for j, ch in enumerate(chunk_words(body)):
                    rec = {
                        "id": f"{doc}#{j}",
                        "doc": doc,
                        "title": title,
                        "date": date,
                        "url": url,
                        "source": source,
                        "pillars": pillars,
                        "text": ch,
                    }
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n_chunks += 1
    print(f"indexed {n_files} articles across {len(date_dirs)} day(s) -> {n_chunks} chunks at {OUT}")


if __name__ == "__main__":
    main()
