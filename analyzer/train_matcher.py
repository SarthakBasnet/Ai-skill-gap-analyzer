"""Training and evaluation helpers used by the submission notebook."""
from __future__ import annotations

import csv
import json
import re
import time
from collections import Counter
from pathlib import Path

import numpy as np

from analyzer.matching import ROOT, load_skill_vocabulary, tokenize

DATA_PATH = ROOT / "data" / "job_dataset.csv"
MODEL_DIR = ROOT / "models"


def load_corpus(path: str | Path = DATA_PATH) -> tuple[list[list[str]], int]:
    docs: list[list[str]] = []
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            # Semicolon-separated entries are retained as text; tokenization later
            # removes punctuation and splits each entry into ordinary word tokens.
            text = " ".join([row.get("Title", ""), row.get("Skills", ""),
                             row.get("Responsibilities", ""), row.get("Keywords", "")])
            docs.append(tokenize(text))
    return docs, sum(map(len, docs))


def mean_embedding(phrase: str, keyed_vectors) -> tuple[np.ndarray | None, list[str]]:
    tokens = tokenize(phrase)
    known = [token for token in tokens if token in keyed_vectors]
    if not known:
        return None, tokens
    return np.mean([keyed_vectors[token] for token in known], axis=0), [t for t in tokens if t not in keyed_vectors]


def train_and_export(seed: int = 17) -> dict:
    from gensim.models import Word2Vec

    docs, word_count = load_corpus()
    counts = Counter(token for doc in docs for token in doc)
    # min_count=2 removes one-off noise while retaining the many job-posting terms.
    params = dict(vector_size=100, window=5, min_count=2, workers=4, sg=1,
                  seed=seed, negative=5, sample=1e-3, epochs=10)
    start = time.perf_counter()
    model = Word2Vec(sentences=docs, **params)
    elapsed = time.perf_counter() - start
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save(str(MODEL_DIR / "word2vec_scratch.model"))

    skills = load_skill_vocabulary()
    skill_embeddings, status = {}, {}
    for skill in skills:
        vector, oov = mean_embedding(skill, model.wv)
        skill_embeddings[skill] = vector.tolist() if vector is not None else None
        status[skill] = {"status": "available" if vector is not None else "no embedding available",
                         "known_words": [w for w in tokenize(skill) if w in model.wv],
                         "oov_words": oov}
    artifact = MODEL_DIR / "skill_embeddings.json"
    artifact.write_text(json.dumps({"skill_embeddings": skill_embeddings,
                                    "skill_embedding_status": status}, indent=2), encoding="utf-8")
    return {"documents": len(docs), "word_count": word_count,
            "vocabulary_after_cleaning": len(counts), "training_vocabulary": len(model.wv),
            "training_seconds": elapsed, "parameters": params,
            "no_embedding_skills": [s for s in skills if skill_embeddings[s] is None],
            "model_path": str(MODEL_DIR / "word2vec_scratch.model"),
            "embeddings_path": str(artifact)}


def evaluate_thresholds(fixture_path: str | Path = ROOT / "tests/fixtures/matching_examples.json") -> tuple[dict, list[dict]]:
    from analyzer.matching import SkillMatcher
    examples = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    matcher = SkillMatcher(threshold=0.0)
    results = matcher.match_many([item["text"] for item in examples])
    records = [{"text": item["text"], "expected": item["skill"],
                "predicted": result.candidates[0][0] if result.candidates else None,
                "confidence": result.confidence}
               for item, result in zip(examples, results)]
    thresholds = {}
    for threshold in np.arange(0.30, 0.81, 0.01):
        correct = sum(r["predicted"] == r["expected"] and r["confidence"] >= threshold for r in records)
        thresholds[round(float(threshold), 2)] = correct / len(records)
    return thresholds, records
