from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Sequence

import random

from .schemas import SplitArtifact


def deterministic_shuffle(ids: list[str], seed: int) -> list[str]:
    rng = random.Random(seed)
    out = list(ids)
    rng.shuffle(out)
    return out


def create_splits(
    example_ids: Sequence[str],
    seed: int,
    train_frac: float = 0.6,
    val_frac: float = 0.2,
    test_frac: float = 0.2,
) -> SplitArtifact:
    assert abs(train_frac + val_frac + test_frac - 1.0) < 1e-6, "fractions must sum to 1"
    ids = deterministic_shuffle(list(example_ids), seed)
    n = len(ids)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)
    train_ids = ids[:n_train]
    val_ids = ids[n_train : n_train + n_val]
    test_ids = ids[n_train + n_val :]
    artifact = SplitArtifact(
        dataset="",
        seed=seed,
        train_ids=train_ids,
        val_ids=val_ids,
        test_ids=test_ids,
    )
    artifact.validate_no_overlap()
    return artifact


def make_split_artifact(
    dataset: str,
    example_ids: Sequence[str],
    seed: int,
    train_frac: float = 0.6,
    val_frac: float = 0.2,
    test_frac: float = 0.2,
) -> SplitArtifact:
    art = create_splits(example_ids, seed, train_frac, val_frac, test_frac)
    art.dataset = dataset
    return art


def save_splits(artifact: SplitArtifact, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(artifact.to_dict(), f, indent=2)


def load_splits(path: str | Path) -> SplitArtifact:
    with open(path) as f:
        d = json.load(f)
    art = SplitArtifact.from_dict(d)
    art.validate_no_overlap()
    return art


def split_path(output_dir: str | Path, dataset: str, seed: int) -> Path:
    return Path(output_dir) / "splits" / dataset / f"seed_{seed}.json"
