"""Skill matching with project-trained Word2Vec vectors (no pretrained weights)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VOCABULARY_PATH = ROOT / "knowledge_base" / "skills.json"
DEFAULT_EMBEDDINGS_PATH = ROOT / "models" / "skill_embeddings.json"
DEFAULT_MODEL_PATH = ROOT / "models" / "word2vec_scratch.model"


@dataclass(frozen=True)
class MatchResult:
    """The best canonical skill match for one input phrase."""

    input_text: str
    matched_skill: str | None
    confidence: float
    matched: bool
    candidates: list[tuple[str, float]]


def tokenize(text: str) -> list[str]:
    """Lowercase and retain alphanumeric tokens; punctuation acts as a boundary."""
    return re.findall(r"[a-z0-9]+", text.lower())


def load_skill_vocabulary(path: str | Path = DEFAULT_VOCABULARY_PATH) -> list[str]:
    with Path(path).open(encoding="utf-8") as file:
        return [skill["name"] for skill in json.load(file)["skills"]]


class SkillMatcher:
    """Average known Word2Vec token vectors and compare them by cosine similarity."""

    def __init__(
        self,
        model_name: str | Path | None = None,
        vocabulary: Sequence[str] | None = None,
        threshold: float = 0.5,
        embeddings_path: str | Path | None = None,
        model_path: str | Path | None = None,
    ) -> None:
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")
        self.threshold = threshold
        self.vocabulary = list(vocabulary) if vocabulary is not None else load_skill_vocabulary()
        if not self.vocabulary:
            raise ValueError("vocabulary must contain at least one skill")
        path = Path(embeddings_path) if embeddings_path else DEFAULT_EMBEDDINGS_PATH
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists():
            raise FileNotFoundError(
                f"Skill embedding artifact not found: {path}. Run the training notebook "
                "notebooks/train_matcher_from_scratch.ipynb first."
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        model_file = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        if not model_file.is_absolute():
            model_file = ROOT / model_file
        if not model_file.exists():
            raise FileNotFoundError(f"Word2Vec model not found: {model_file}. Run the training notebook first.")
        try:
            from gensim.models import Word2Vec
        except ImportError as exc:
            raise RuntimeError("gensim is required to load the trained Word2Vec model") from exc
        self.model = Word2Vec.load(str(model_file))
        self._word_vectors = self.model.wv
        stored = payload.get("skill_embeddings", {})
        self.skill_embedding_status = payload.get("skill_embedding_status", {})
        self._skill_vectors = {
            skill: np.asarray(stored[skill], dtype=np.float32)
            for skill in self.vocabulary if stored.get(skill) is not None
        }
        self._skills = list(self._skill_vectors)
        self._matrix = self._normalize(np.stack([self._skill_vectors[s] for s in self._skills])) if self._skills else np.empty((0, 0))

    @staticmethod
    def _normalize(vector: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vector, axis=-1, keepdims=True)
        return np.divide(vector, norms, out=np.zeros_like(vector), where=norms != 0)

    def embed(self, text: str) -> np.ndarray | None:
        vectors = [self._word_vectors[word] for word in tokenize(text) if word in self._word_vectors]
        if not vectors:
            return None
        mean = np.mean(vectors, axis=0)
        if not np.linalg.norm(mean):
            return None
        return self._normalize(mean)

    def _results(self, texts: Sequence[str]) -> list[MatchResult]:
        results = []
        for text in texts:
            vector = self.embed(text)
            if vector is None or not self._skills:
                results.append(MatchResult(text, None, 0.0, False, []))
                continue
            scores = self._matrix @ vector
            indexes = np.argsort(-scores, kind="stable")[:3]
            candidates = [(self._skills[i], float(np.clip(scores[i], 0, 1))) for i in indexes]
            best, confidence = candidates[0]
            matched = confidence >= self.threshold
            results.append(MatchResult(text, best if matched else None, confidence, matched, candidates))
        return results

    def match(self, text: str) -> MatchResult:
        return self._results([text])[0]

    def match_many(self, texts: list[str]) -> list[MatchResult]:
        return self._results(texts)
