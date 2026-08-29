from __future__ import annotations

from ..data.scoring import parse_answer, score_example


def parse_and_score(completion: str, gold: str, scoring: str) -> tuple[str | None, bool]:
    parsed = parse_answer(completion, scoring)
    correct = score_example(parsed, gold, scoring)
    return parsed, correct
