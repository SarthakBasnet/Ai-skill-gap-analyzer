import json
import sys
import types

import numpy as np
import pytest

from analyzer.eval_matching import evaluate
from analyzer.matching import MatchResult, SkillMatcher, load_skill_vocabulary, tokenize


class FakeVectors(dict):
    def __contains__(self, word):
        return dict.__contains__(self, word)


class FakeWord2Vec:
    wv = FakeVectors({
        "sql": np.array([1.0, 0.0]), "wrote": np.array([1.0, 0.0]),
        "queries": np.array([1.0, 0.0]), "nosql": np.array([0.0, 1.0]),
        "databases": np.array([0.0, 1.0]),
    })

    @classmethod
    def load(cls, path):
        return cls()


@pytest.fixture
def matcher(tmp_path, monkeypatch):
    gensim = types.ModuleType("gensim")
    models = types.ModuleType("gensim.models")
    models.Word2Vec = FakeWord2Vec
    gensim.models = models
    monkeypatch.setitem(sys.modules, "gensim", gensim)
    monkeypatch.setitem(sys.modules, "gensim.models", models)
    model_path = tmp_path / "word2vec.model"
    model_path.write_bytes(b"test placeholder")
    embeddings_path = tmp_path / "skills.json"
    embeddings_path.write_text(json.dumps({
        "skill_embeddings": {"SQL": [1.0, 0.0], "NoSQL": [0.0, 1.0]},
        "skill_embedding_status": {},
    }), encoding="utf-8")
    return SkillMatcher(vocabulary=["SQL", "NoSQL"], model_path=model_path,
                        embeddings_path=embeddings_path)


def test_load_skill_vocabulary_has_unique_canonical_names():
    vocabulary = load_skill_vocabulary()
    assert len(vocabulary) == 67
    assert len(vocabulary) == len(set(vocabulary))


def test_cleaning_lowercases_and_strips_punctuation():
    assert tokenize("CI/CD, Power BI; C#") == ["ci", "cd", "power", "bi", "c"]


def test_known_phrase_matches_by_cosine_and_no_sql_trap(matcher):
    assert matcher.match("wrote SQL queries").matched_skill == "SQL"
    assert matcher.match("used NoSQL databases").matched_skill == "NoSQL"


def test_all_oov_phrase_is_rejected_with_no_candidates(matcher):
    result = matcher.match("unseen jargon")
    assert result == MatchResult("unseen jargon", None, 0.0, False, [])


def test_threshold_gates_prediction_but_retains_candidates(matcher):
    matcher.threshold = 1.0
    result = matcher.match("sql databases")
    assert not result.matched
    assert result.matched_skill is None
    assert len(result.candidates) == 2


def test_batch_matching_preserves_order(matcher):
    results = matcher.match_many(["SQL", "NoSQL"])
    assert [result.matched_skill for result in results] == ["SQL", "NoSQL"]


def test_evaluation_fixture_is_loaded_without_claiming_accuracy(matcher):
    accuracy, records = evaluate(matcher)
    assert len(records) == 154
    assert 0.0 <= accuracy <= 1.0
