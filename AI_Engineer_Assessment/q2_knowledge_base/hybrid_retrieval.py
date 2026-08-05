"""
Hybrid retrieval for the CareShield knowledge base.

Combines two signals so retrieval doesn't depend on exact keyword overlap
alone, without requiring a downloaded embedding model:

1. BM25 (rank_bm25) — lexical/keyword relevance, strong on exact terms like
   plan names, dollar amounts, "pre-existing conditions".
2. TF-IDF cosine similarity (scikit-learn) — softer term-weighted overlap,
   catches paraphrases BM25's term-frequency saturation can miss.

Scores are min-max normalized per-query and combined with a weighted sum
(BM25_WEIGHT / TFIDF_WEIGHT below). A CONFIDENCE_THRESHOLD gates whether we
return an answer at all — if nothing clears it, the caller gets an honest
"not found" instead of the weakest available match. This is what lets the
voice agent say "I don't have that confirmed" instead of hallucinating.

Swap-in path for a real embedding model (e.g. sentence-transformers) once
you have network access to download weights: replace `_tfidf_scores` with
cosine similarity over the embedding matrix — the fusion/threshold logic
below doesn't need to change.
"""

import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent.parent
KB_PATH = BASE_DIR / "knowledge_base_records.json"

BM25_WEIGHT = 0.5
TFIDF_WEIGHT = 0.5
CONFIDENCE_THRESHOLD = 0.20  # below this fused (normalized) score -> no match
MIN_RAW_TFIDF_COSINE = 0.15  # absolute floor on raw TF-IDF cosine, see note
TOP_K = 3

# NOTE on MIN_RAW_TFIDF_COSINE: with a small corpus, per-query min-max
# normalization always stretches the *best available* result toward 1.0,
# even when every candidate is a poor match — "best of a bad bunch" still
# looks confident after normalization alone, and raw BM25 has the same
# problem since it's unbounded and inflates on generic shared tokens.
# Confirmed this empirically: a query with no real overlap ("claims refund
# turnaround for a surgery in Mumbai") still scored a fused 0.5 and a raw
# BM25 of 1.2 — close to genuine matches. Raw (pre-normalization) TF-IDF
# cosine similarity turned out to be the clean signal: it was exactly 0.0
# for the true negative and >=0.24 for every genuine match tested. Gating
# on it catches false positives the fused/BM25 scores alone don't. Re-tune
# this floor once the KB is larger and score distributions stabilize.


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _normalize(scores):
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-9:
        return [0.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


class KnowledgeBase:
    def __init__(self, records_path: Path = KB_PATH):
        with open(records_path, "r", encoding="utf-8") as f:
            self.records = json.load(f)

        self.corpus = [f"{r['title']} {r['content']}" for r in self.records]
        self.tokenized_corpus = [_tokenize(doc) for doc in self.corpus]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)

    def _bm25_scores(self, query: str):
        return list(self.bm25.get_scores(_tokenize(query)))

    def _tfidf_scores(self, query: str):
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        return list(sims)

    def search(self, query: str, top_k: int = TOP_K):
        bm25_raw = self._bm25_scores(query)
        tfidf_cosine_raw = self._tfidf_scores(query)

        bm25_norm = _normalize(bm25_raw)
        tfidf_norm = _normalize(tfidf_cosine_raw)

        fused = [
            BM25_WEIGHT * b + TFIDF_WEIGHT * t
            for b, t in zip(bm25_norm, tfidf_norm)
        ]

        ranked = sorted(
            range(len(self.records)), key=lambda i: fused[i], reverse=True
        )[:top_k]

        results = []
        for i in ranked:
            record = self.records[i]
            results.append(
                {
                    "record_id": record["record_id"],
                    "title": record["title"],
                    "content": record["content"],
                    "source": record["source"],
                    "category": record["category"],
                    "score": float(round(fused[i], 4)),
                    "bm25_score": float(round(bm25_norm[i], 4)),
                    "tfidf_score": float(round(tfidf_norm[i], 4)),
                    "bm25_raw": float(round(bm25_raw[i], 4)),
                    "tfidf_cosine_raw": float(round(tfidf_cosine_raw[i], 4)),
                }
            )
        return results

    def answer(self, query: str, top_k: int = TOP_K):
        """Returns top matches plus a confidence gate for the voice agent."""
        results = self.search(query, top_k=top_k)
        best = results[0] if results else None
        confident = bool(
            best is not None
            and best["score"] >= CONFIDENCE_THRESHOLD
            and best["tfidf_cosine_raw"] >= MIN_RAW_TFIDF_COSINE
        )
        return {
            "query": query,
            "confident": confident,
            "results": results if confident else [],
            "fallback_message": (
                None
                if confident
                else "I don't have that information confirmed right now."
            ),
        }


if __name__ == "__main__":
    kb = KnowledgeBase()
    demo_queries = [
        "What is the waiting period for pre-existing conditions?",
        "How much does the Gold Plan cost per month?",
    ]
    for q in demo_queries:
        result = kb.answer(q)
        print(json.dumps(result, indent=2))
