from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import torch
except ImportError:
    torch = None  # type: ignore


def activation_path(
    output_dir: str | Path,
    dataset: str,
    model: str,
    condition: str,
    mode: str,
    layer: int,
    seed: int,
) -> Path:
    safe_model = model.replace("/", "__")
    return Path(output_dir) / "activations" / dataset / safe_model / condition / mode / f"layer_{layer}" / f"seed_{seed}.pt"


def save_activations(
    path: str | Path,
    activations: Any,  # dict example_id -> tensor or np array
    meta: dict[str, Any],
) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if torch is not None and isinstance(list(activations.values())[0] if activations else None, torch.Tensor):
        torch.save({"activations": activations, "meta": meta}, p)
    else:
        # numpy fallback via torch or pickle
        import pickle

        with open(p, "wb") as f:
            pickle.dump({"activations": activations, "meta": meta}, f)


def load_activations(path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    p = Path(path)
    if torch is not None:
        try:
            data = torch.load(p, map_location="cpu")
            return data["activations"], data["meta"]
        except Exception:
            pass
    import pickle

    with open(p, "rb") as f:
        data = pickle.load(f)
    return data["activations"], data["meta"]
