from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ..data.schemas import GenerationRecord


def generation_path(output_dir: str | Path, dataset: str, model: str, condition: str, seed: int) -> Path:
    # sanitize model name for filesystem
    safe_model = model.replace("/", "__")
    return Path(output_dir) / "generations" / dataset / safe_model / condition / f"seed_{seed}.jsonl"


def write_generations(records: Iterable[GenerationRecord], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        for r in records:
            r.validate()
            f.write(json.dumps(r.to_dict()) + "\n")


def read_generations(path: str | Path) -> list[GenerationRecord]:
    records = []
    with open(path) as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                records.append(GenerationRecord(**d))
    return records


def load_all_generations(output_dir: str | Path, dataset: str | None = None) -> list[GenerationRecord]:
    base = Path(output_dir) / "generations"
    if not base.exists():
        return []
    out = []
    for p in base.rglob("seed_*.jsonl"):
        if dataset and dataset not in str(p):
            continue
        out.extend(read_generations(p))
    return out
