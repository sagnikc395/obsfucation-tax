from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(
    default_path: str | Path = "configs/default.yaml",
    extra_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    """Load merged config. No hardcoded model/dataset/layer inside logic."""
    config: dict[str, Any] = {}
    if Path(default_path).exists():
        config = load_yaml(default_path)
    # overlay other config files if listed
    config_dir = Path(default_path).parent
    for name in ["models.yaml", "datasets.yaml", "prompts.yaml", "probes.yaml", "monitors.yaml", "red_team.yaml"]:
        p = config_dir / name
        if p.exists():
            data = load_yaml(p)
            # namespace under key derived from filename to avoid collisions
            key = name.replace(".yaml", "")
            config[key] = data

    if extra_paths:
        for p in extra_paths:
            if Path(p).exists():
                config = deep_merge(config, load_yaml(p))

    # env override: OBFUSC_* not needed now
    return config


def get_output_dir(config: dict[str, Any]) -> Path:
    return Path(config.get("output_dir", "artifacts"))


def resolve_device(config: dict[str, Any]) -> str:
    device = config.get("device", "auto")
    if device != "auto":
        return device
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    except ImportError:
        return "cpu"
