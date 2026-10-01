"""Embedding-based matching of free-text skill descriptions to canonical skills."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_VOCABULARY_PATH = Path("knowledge_base/skills.json")


@dataclass(frozen=True)
class MatchResult:
    """The best canonical skill match for one input phrase."""

    input_text: str
    matched_skill: str | None
    confidence: float
    matched: bool
    candidates: list[tuple[str, float]]


def load_skill_vocabulary(path: str | Path = DEFAULT_VOCABULARY_PATH) -> list[str]:
    """Load canonical skill names from the project skill taxonomy."""

    with Path(path).open(encoding="utf-8") as file:
        data = json.load(file)
    return [skill["name"] for skill in data["skills"]]


class SkillMatcher:
    """Match free text against a fixed canonical skill vocabulary."""

    def __init__(
        self,
        model_name: str | Path = "all-MiniLM-L6-v2",
        vocabulary: Sequence[str] | None = None,
        threshold: float = 0.55,
    ) -> None:
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")

        self.threshold = threshold
        self.vocabulary = list(vocabulary) if vocabulary is not None else load_skill_vocabulary()
        if not self.vocabulary:
            raise ValueError("vocabulary must contain at least one skill")

        # In Django, create this instance once at app start-up, not per request.
        self.model = SentenceTransformer(model_name)
        self._vocabulary_embeddings = self.model.encode(
            self.vocabulary,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def _results(self, texts: Sequence[str]) -> list[MatchResult]:
        if not texts:
            return []
        embeddings = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        embeddings = np.atleast_2d(embeddings)
        similarities = embeddings @ self._vocabulary_embeddings.T

        results: list[MatchResult] = []
        for text, scores in zip(texts, similarities):
            ranked_indexes = np.argsort(-scores, kind="stable")
            candidates = [
                (self.vocabulary[index], float(np.clip(scores[index], 0.0, 1.0)))
                for index in ranked_indexes[:3]
            ]
            best_index = int(ranked_indexes[0])
            best_score = float(np.clip(scores[best_index], 0.0, 1.0))
            matched = best_score >= self.threshold
            results.append(
                MatchResult(
                    input_text=text,
                    matched_skill=self.vocabulary[best_index] if matched else None,
                    confidence=best_score,
                    matched=matched,
                    candidates=candidates,
                )
            )
        return results

    def match(self, text: str) -> MatchResult:
        """Return the best match for one free-text phrase."""

        return self._results([text])[0]

    def match_many(self, texts: list[str]) -> list[MatchResult]:
        """Batch-match phrases while preserving their input order."""

        return self._results(texts)
