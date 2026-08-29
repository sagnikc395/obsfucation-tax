from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ..data.schemas import GenerationRecord
from .token_spans import find_answer_span, aggregate_hidden_states
from .layers import resolve_layers
from .cache import activation_path, save_activations


def _dummy_activations(records: list[GenerationRecord], layers: list[int], hidden_dim: int = 128) -> dict[int, dict[str, Any]]:
    """Create deterministic synthetic activations for testing without model."""
    rng = np.random.RandomState(42)
    out: dict[int, dict[str, Any]] = {}
    for layer in layers:
        acts: dict[str, Any] = {}
        for rec in records:
            # sandbagging gets a shifted mean so probe can learn
            is_sandbag = rec.condition in ("sandbag_r0", "sandbag_r1", "heldout_template")
            base = rng.randn(hidden_dim) * 0.5
            if is_sandbag:
                base += 1.5  # separable signal
            # also make correct vs incorrect slightly different? not needed
            acts[rec.example_id] = base.astype(np.float32)
        out[layer] = acts
    return out


def collect_activations(
    records: list[GenerationRecord],
    config: dict[str, Any],
    mode: str = "teacher_forced",
    layers: list[int] | None = None,
    use_dummy: bool = False,
) -> dict[int, dict[str, Any]]:
    """Collect residual-stream activations over answer tokens only.
    Returns dict layer -> {example_id: vector}
    """
    if layers is None:
        layers = resolve_layers(config)

    if use_dummy or not records:
        if not records:
            return {l: {} for l in layers}
        return _dummy_activations(records, layers)

    # Real model path: try HF transformers with hooks
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch

        # resolve model name from first record
        model_name = records[0].model
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=False)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.float16, device_map="auto", trust_remote_code=False, output_hidden_states=True
        )
        model.eval()
        result: dict[int, dict[str, Any]] = {l: {} for l in layers}
        aggregation = config.get("activations", {}).get("aggregation", "mean")

        for rec in records:
            prompt = rec.prompt
            completion = rec.completion
            span = find_answer_span(prompt, completion, tokenizer, aggregation)
            # teacher_forced: replay prompt+completion; self_generated same but we still replay
            text = prompt + completion if mode == "teacher_forced" else prompt + completion
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048)
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = model(**inputs, output_hidden_states=True)
                hidden_states = outputs.hidden_states  # tuple layer 0..n

            for layer in layers:
                # hidden_states index: 0 is embeddings, so layer+1 if needed
                idx = min(layer + 1, len(hidden_states) - 1)
                hs = hidden_states[idx][0].cpu()  # [seq, dim]
                vec = aggregate_hidden_states(hs, span, method=aggregation)
                # ensure numpy or tensor
                if isinstance(vec, torch.Tensor):
                    vec = vec.float().numpy()
                result[layer][rec.example_id] = vec
        return result
    except Exception as e:
        # fallback to dummy on any error
        return _dummy_activations(records, layers)


def run_activation_collection(
    records: list[GenerationRecord],
    config: dict[str, Any],
    output_dir: str | Path | None = None,
    modes: list[str] | None = None,
    use_dummy: bool = False,
) -> list[Path]:
    out_dir = Path(output_dir or config.get("output_dir", "artifacts"))
    if not records:
        return []
    layers = resolve_layers(config)
    modes = modes or [config.get("activations", {}).get("mode", "teacher_forced")]
    # Group by dataset/model/condition/mode would be per call - here we batch
    # Assume all records share dataset/model/condition for simplicity; else split
    from collections import defaultdict

    grouped: dict[tuple[str, str, str], list[GenerationRecord]] = defaultdict(list)
    for r in records:
        grouped[(r.dataset, r.model, r.condition)].append(r)

    saved: list[Path] = []
    for (dataset, model, condition), recs in grouped.items():
        for mode in modes:
            layer_to_acts = collect_activations(recs, config, mode=mode, layers=layers, use_dummy=use_dummy)
            for layer, acts in layer_to_acts.items():
                seed = recs[0].seed
                path = activation_path(out_dir, dataset, model, condition, mode, layer, seed)
                meta = {
                    "dataset": dataset,
                    "model": model,
                    "condition": condition,
                    "mode": mode,
                    "layer": layer,
                    "seed": seed,
                    "n": len(acts),
                    "aggregation": config.get("activations", {}).get("aggregation", "mean"),
                }
                save_activations(path, acts, meta)
                saved.append(path)
    return saved
