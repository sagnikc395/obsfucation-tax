from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Example:
    example_id: str
    dataset: str
    split: str
    question: str
    gold_answer: str
    choices: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationRecord:
    example_id: str
    dataset: str
    split: str
    condition: str
    seed: int
    prompt_template_id: str
    prompt: str
    completion: str
    parsed_answer: str | None
    gold_answer: str
    correct: bool | None
    model: str
    model_revision: str | None = None
    decoding_settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def required_fields(cls) -> list[str]:
        return [
            "example_id",
            "dataset",
            "split",
            "condition",
            "seed",
            "prompt_template_id",
            "prompt",
            "completion",
            "parsed_answer",
            "gold_answer",
            "correct",
            "model",
            "decoding_settings",
        ]

    def validate(self) -> None:
        for f in self.required_fields():
            if not hasattr(self, f):
                raise ValueError(f"Missing field {f}")
        # parsed_answer may be None but field must exist
        # prompt/completion must be non-empty
        if not self.prompt:
            raise ValueError("prompt must be non-empty")
        if self.completion is None:
            raise ValueError("completion must not be None")


@dataclass
class ActivationMeta:
    example_id: str
    dataset: str
    condition: str
    mode: str  # teacher_forced | self_generated
    layer: int
    seed: int
    token_span: tuple[int, int]  # answer token start, end (exclusive)
    shape: tuple[int, ...]


@dataclass
class ProbeMetrics:
    dataset: str
    model: str
    layer: int
    seed: int
    auroc: float
    accuracy: float
    auprc: float | None = None
    ece: float | None = None
    n_train: int | None = None
    n_val: int | None = None
    n_test: int | None = None


@dataclass
class SplitArtifact:
    dataset: str
    seed: int
    train_ids: list[str]
    val_ids: list[str]
    test_ids: list[str]

    def validate_no_overlap(self) -> None:
        t, v, te = set(self.train_ids), set(self.val_ids), set(self.test_ids)
        if t & v:
            raise ValueError(f"train/val overlap: {t & v}")
        if t & te:
            raise ValueError(f"train/test overlap: {t & te}")
        if v & te:
            raise ValueError(f"val/test overlap: {v & te}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SplitArtifact":
        return cls(**d)
