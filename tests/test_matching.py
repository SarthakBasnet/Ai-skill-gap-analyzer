import pytest

from analyzer.eval_matching import evaluate
from analyzer.matching import SkillMatcher, load_skill_vocabulary


def test_matcher_accepts_an_explicit_local_model_path(tmp_path, monkeypatch):
    """An explicitly supplied local model path is passed through to SentenceTransformer."""
    model_path = tmp_path / "local-model"
    model_path.mkdir()
    loaded = {}

    class FakeModel:
        def __init__(self, model_name):
            loaded["model_name"] = model_name

        def encode(self, texts, **kwargs):
            import numpy as np

            return np.ones((len(texts), 3), dtype=float)

    monkeypatch.setattr("analyzer.matching.SentenceTransformer", FakeModel)
    matcher = SkillMatcher(model_name=model_path, vocabulary=["SQL"])
    assert loaded["model_name"] == model_path
    assert matcher.vocabulary == ["SQL"]


@pytest.fixture(scope="module")
def matcher():
    """Share the expensive model load across matcher tests."""

    return SkillMatcher()


def test_load_skill_vocabulary_has_unique_canonical_names():
    vocabulary = load_skill_vocabulary()
    assert len(vocabulary) >= 60
    assert len(vocabulary) == len(set(vocabulary))


@pytest.mark.slow
def test_exact_skill_name_matches_itself(matcher):
    result = matcher.match("SQL")
    assert result.matched_skill == "SQL"
    assert result.confidence > 0.9


@pytest.mark.slow
def test_clear_paraphrase_matches_sql(matcher):
    result = matcher.match("wrote SQL queries")
    assert result.matched_skill == "SQL"
    assert result.matched


@pytest.mark.slow
def test_unrelated_input_is_rejected(matcher):
    result = matcher.match("I like pizza")
    assert not result.matched
    assert result.matched_skill is None
    assert len(result.candidates) == 3


@pytest.mark.slow
def test_nosql_trap_does_not_match_sql(matcher):
    result = matcher.match("used NoSQL databases")
    assert result.matched_skill == "NoSQL"
    assert result.matched_skill != "SQL"


@pytest.mark.slow
def test_match_many_preserves_order_and_matches_single_calls(matcher):
    texts = ["wrote SQL queries", "built REST endpoints", "I like pizza"]
    batch_results = matcher.match_many(texts)
    individual_results = [matcher.match(text) for text in texts]
    assert [result.input_text for result in batch_results] == texts
    for batch, individual in zip(batch_results, individual_results):
        assert batch.matched_skill == individual.matched_skill
        assert batch.matched == individual.matched
        assert batch.confidence == pytest.approx(individual.confidence, abs=1e-6)
        assert [skill for skill, _ in batch.candidates] == [skill for skill, _ in individual.candidates]


@pytest.mark.slow
def test_evaluation_fixture_reaches_realistic_accuracy_bar(matcher):
    accuracy, records = evaluate(matcher)
    assert len(records) >= 40
    assert accuracy >= 0.60
