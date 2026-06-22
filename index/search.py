#!/usr/bin/env python3
"""BM25 search over the ai-news industry corpus chunks (index/chunks.jsonl).

Pure-Python, no dependencies. Usage:
  python3 index/search.py "CoWoS HBM supply allocation" --k 8
  python3 index/search.py "hyperscaler capex digestion" --k 6 --json

Returns the most relevant primary-source passages with date / source / title / url so a
reader can ground a verdict in what the industry literature actually reported. This is the
retrieval engine behind the trading-analysis "Industry Brain".
"""
import argparse, json, math, os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNKS = os.path.join(ROOT, "index", "chunks.jsonl")

STOP = set("the a an and or of to in is are was were be been being for on at by with as it its "
           "this that these those i you he she we they them his her our your their my me us "
           "do does did have has had will would can could should may might must not no so if "
           "but about into over under than then there here what which who whom how why when "
           "uh um yeah okay ok know like just really very thing things gonna going get got".split())

TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text):
    return [t for t in TOKEN.findall(text.lower()) if len(t) > 1 and t not in STOP]


def load():
    docs = []
    with open(CHUNKS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.toks = [tokenize(d["text"]) for d in docs]
        self.len = [len(t) for t in self.toks]
        self.avg = sum(self.len) / max(1, len(self.len))
        self.tf = [Counter(t) for t in self.toks]
        df = Counter()
        for t in self.toks:
            df.update(set(t))
        N = len(docs)
        self.idf = {term: math.log(1 + (N - n + 0.5) / (n + 0.5)) for term, n in df.items()}

    def score(self, qterms, i):
        s = 0.0
        tf, dl = self.tf[i], self.len[i]
        for term in qterms:
            if term not in tf:
                continue
            f = tf[term]
            idf = self.idf.get(term, 0.0)
            s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self.avg))
        return s

    def search(self, query, k=8, per_doc=2):
        qterms = tokenize(query)
        scored = [(self.score(qterms, i), i) for i in range(len(self.docs))]
        scored = [x for x in scored if x[0] > 0]
        scored.sort(reverse=True)
        out, seen = [], Counter()
        for sc, i in scored:
            d = self.docs[i]
            if seen[d["doc"]] >= per_doc:
                continue
            seen[d["doc"]] += 1
            out.append((sc, d))
            if len(out) >= k:
                break
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="+")
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--per-doc", type=int, default=2)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    query = " ".join(args.query)
    if not os.path.exists(CHUNKS):
        sys.exit("index/chunks.jsonl not found - run index/build_index.py first")
    bm = BM25(load())
    hits = bm.search(query, k=args.k, per_doc=args.per_doc)
    if args.json:
        print(json.dumps([{"score": round(s, 3), **d} for s, d in hits], ensure_ascii=False, indent=2))
        return
    if not hits:
        print(f"No matches for: {query}")
        return
    print(f"Query: {query}   ({len(hits)} passages)\n")
    for rank, (s, d) in enumerate(hits, 1):
        print(f"[{rank}] score={s:.2f}  {d['date']}  [{d.get('source','')}]  {d['title'][:64]}")
        print(f"    {d['url']}")
        print(f"    …{d['text'].strip()}…\n")


if __name__ == "__main__":
    main()
