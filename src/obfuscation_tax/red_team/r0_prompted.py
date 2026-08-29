from __future__ import annotations

from typing import Any

from ..data.schemas import Example
from ..generation.runner import generate_for_examples


def run_r0(
    examples: list[Example],
    config: dict[str, Any],
    seed: int,
    model_key: str | None = None,
    use_dummy: bool = False,
):
    return generate_for_examples(examples, condition="sandbag_r0", config=config, seed=seed, model_key=model_key, use_dummy=use_dummy)
