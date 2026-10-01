"""Evaluate the standalone skill matcher against the hand-labelled fixture."""

from __future__ import annotations

import json
from pathlib import Path

from analyzer.matching import SkillMatcher


FIXTURE_PATH = Path(__file__).parents[1] / "tests" / "fixtures" / "matching_examples.json"


def evaluate(matcher: SkillMatcher | None = None) -> tuple[float, list[dict[str, object]]]:
    """Return accuracy and per-example result records for the labelled fixture."""

    examples = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    matcher = matcher or SkillMatcher()
    results = matcher.match_many([example["text"] for example in examples])
    records = []
    for example, result in zip(examples, results):
        records.append(
            {
                "text": example["text"],
                "expected": example["skill"],
                "actual": result.matched_skill,
                "confidence": result.confidence,
                "correct": result.matched_skill == example["skill"],
            }
        )
    accuracy = sum(record["correct"] for record in records) / len(records)
    return accuracy, records


def main() -> None:
    accuracy, records = evaluate()
    for record in records:
        status = "OK" if record["correct"] else "WRONG"
        print(
            f"[{status}] {record['text']!r} -> {record['actual']!r} "
            f"(expected {record['expected']!r}, confidence={record['confidence']:.3f})"
        )
    print(f"Top-1 accuracy: {accuracy:.1%} ({sum(record['correct'] for record in records)}/{len(records)})")


if __name__ == "__main__":
    main()
