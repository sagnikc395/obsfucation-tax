from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from .schemas import Example
from .splits import make_split_artifact, save_splits, split_path


def _synthetic_examples(dataset: str, n: int, seed: int = 0) -> list[Example]:
    rng = random.Random(seed)
    examples = []
    for i in range(n):
        q = f"Synthetic question {i}: What is {rng.randint(0,3)}? Choices: A)0 B)1 C)2 D)3"
        gold = rng.choice(["A", "B", "C", "D"])
        examples.append(
            Example(
                example_id=f"{dataset}_{i:05d}",
                dataset=dataset,
                split="train",
                question=q,
                gold_answer=gold,
                choices=["A", "B", "C", "D"],
                metadata={"synthetic": True},
            )
        )
    return examples


def load_dataset(
    dataset: str,
    config: dict[str, Any],
    seed: int = 42,
    split: str | None = None,
) -> list[Example]:
    """Load dataset via HF datasets if available, else synthetic fallback."""
    ds_cfg = config.get("datasets", {}).get("datasets", {}).get(dataset, {})
    hf_name = ds_cfg.get("hf_name")

    # Try HF datasets
    if hf_name:
        try:
            from datasets import load_dataset as hf_load

            hf = hf_load(hf_name, ds_cfg.get("subset") or None)
            # normalize: expect splits available
            examples: list[Example] = []
            # handle MMLU: test split contains all, GSM8K train/test
            for hf_split in hf.keys():
                split_ds = hf[hf_split]
                limit = ds_cfg.get(f"n_{split}") if split else None
                for idx, row in enumerate(split_ds):
                    # row shape varies
                    q = row.get("question") or row.get("input") or str(row)
                    # MMLU has choices + answer (0-3)
                    if "choices" in row and "answer" in row:
                        choices = row["choices"]
                        ans_idx = row["answer"]
                        gold = choices[ans_idx] if isinstance(ans_idx, int) else str(ans_idx)
                        # map to letter
                        if gold in choices:
                            gold = chr(65 + choices.index(gold))
                        else:
                            gold = str(gold)
                        q_full = f"{q}\nChoices: " + ", ".join(f"{chr(65+i)}) {c}" for i, c in enumerate(choices))
                    elif "answer" in row:
                        gold = str(row["answer"]).split("####")[-1].strip() if "####" in str(row["answer"]) else str(row["answer"])
                        q_full = q
                        choices = None
                    else:
                        gold = str(row.get("label", "A"))
                        q_full = q
                        choices = None
                    examples.append(
                        Example(
                            example_id=f"{dataset}_{hf_split}_{idx:05d}",
                            dataset=dataset,
                            split=hf_split,
                            question=q_full,
                            gold_answer=gold,
                            choices=choices,
                        )
                    )
                    if split and len([e for e in examples if e.split == split]) >= (limit or 10**9):
                        break
            if split:
                examples = [e for e in examples if e.split == split]
            if examples:
                return examples
        except Exception as e:
            # fallback to synthetic
            pass

    # Synthetic fallback
    n = ds_cfg.get("n_train", 100) + ds_cfg.get("n_val", 20) + ds_cfg.get("n_test", 20) if not split else ds_cfg.get(f"n_{split}", 50)
    return _synthetic_examples(dataset, n=n, seed=seed)


def prepare_splits_for_dataset(
    dataset: str,
    config: dict[str, Any],
    seed: int = 42,
    output_dir: str | Path = "artifacts",
) -> Path:
    examples = load_dataset(dataset, config, seed=seed)
    ids = [e.example_id for e in examples]
    splits_cfg = config.get("splits", {"train": 0.6, "validation": 0.2, "test": 0.2})
    # handle key naming: validation vs val
    train_frac = splits_cfg.get("train", 0.6)
    val_frac = splits_cfg.get("validation", splits_cfg.get("val", 0.2))
    test_frac = splits_cfg.get("test", 0.2)
    artifact = make_split_artifact(dataset, ids, seed, train_frac, val_frac, test_frac)
    path = split_path(output_dir, dataset, seed)
    save_splits(artifact, path)
    return path
