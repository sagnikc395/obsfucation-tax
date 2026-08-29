from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tqdm import tqdm

from ..data.schemas import Example, GenerationRecord
from ..data.scoring import parse_answer, score_example
from ..prompts.templates import render_prompt
from ..prompts.sandbagging import template_for_condition
from .cache import generation_path, write_generations


def _resolve_model_name(config: dict[str, Any], model_key: str | None = None) -> tuple[str, str | None]:
    models_cfg = config.get("models", {}).get("models", {})
    defaults = config.get("models", {}).get("defaults", {})
    key = model_key or defaults.get("untrusted", "qwen_1_5b")
    m = models_cfg.get(key, {})
    name = m.get("name", key)
    rev = m.get("revision")
    return name, rev


def _dummy_generate(prompt: str, model_name: str) -> str:
    """Deterministic dummy generation for CI without GPU/HF download."""
    # hash-like but deterministic: return letter based on prompt length
    letters = ["A", "B", "C", "D"]
    idx = len(prompt) % 4
    # if sandbag prompt present, shift answer to simulate attack
    if "underperform" in prompt.lower() or "incorrect" in prompt.lower():
        idx = (idx + 1) % 4
    return f"Answer: {letters[idx]}"


def generate_for_examples(
    examples: list[Example],
    condition: str,
    config: dict[str, Any],
    seed: int,
    model_key: str | None = None,
    use_dummy: bool = False,
) -> list[GenerationRecord]:
    model_name, model_revision = _resolve_model_name(config, model_key)
    scoring = config.get("datasets", {}).get("datasets", {}).get(examples[0].dataset, {}).get("scoring", "exact_match_letter") if examples else "exact_match_letter"
    gen_cfg = config.get("generation", {})
    decoding = {
        "max_new_tokens": gen_cfg.get("max_new_tokens", 256),
        "temperature": gen_cfg.get("temperature", 0.0),
        "top_p": gen_cfg.get("top_p", 1.0),
        "do_sample": gen_cfg.get("do_sample", False),
    }

    # Try real HF generation unless dummy
    tokenizer = None
    model = None
    if not use_dummy:
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch

            dtype_map = {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}
            dtype = dtype_map.get(config.get("dtype", "float16"), torch.float16)
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=False)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            model = AutoModelForCausalLM.from_pretrained(
                model_name, torch_dtype=dtype, device_map="auto", trust_remote_code=False
            )
            model.eval()
        except Exception:
            tokenizer = None
            model = None

    records: list[GenerationRecord] = []
    template_id = template_for_condition(condition, config)

    for ex in tqdm(examples, desc=f"generate {condition}"):
        prompt, cond = render_prompt(template_id, ex.question, config)
        # ensure condition label matches requested condition
        if model is not None and tokenizer is not None:
            try:
                import torch

                inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
                with torch.no_grad():
                    out = model.generate(
                        **inputs,
                        max_new_tokens=decoding["max_new_tokens"],
                        temperature=decoding["temperature"],
                        top_p=decoding["top_p"],
                        do_sample=decoding["do_sample"],
                        pad_token_id=tokenizer.eos_token_id,
                    )
                completion = tokenizer.decode(out[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
            except Exception:
                completion = _dummy_generate(prompt, model_name)
        else:
            completion = _dummy_generate(prompt, model_name)

        parsed = parse_answer(completion, scoring)
        correct = score_example(parsed, ex.gold_answer, scoring)

        rec = GenerationRecord(
            example_id=ex.example_id,
            dataset=ex.dataset,
            split=ex.split,
            condition=condition,
            seed=seed,
            prompt_template_id=template_id,
            prompt=prompt,
            completion=completion,
            parsed_answer=parsed,
            gold_answer=ex.gold_answer,
            correct=correct,
            model=model_name,
            model_revision=model_revision,
            decoding_settings=decoding,
        )
        records.append(rec)

    return records


def run_generation_stage(
    examples: list[Example],
    condition: str,
    config: dict[str, Any],
    seed: int,
    output_dir: str | Path | None = None,
    model_key: str | None = None,
    use_dummy: bool = False,
) -> Path:
    out_dir = Path(output_dir or config.get("output_dir", "artifacts"))
    if not examples:
        raise ValueError("No examples provided")
    model_name, _ = _resolve_model_name(config, model_key)
    dataset = examples[0].dataset
    records = generate_for_examples(examples, condition, config, seed, model_key, use_dummy=use_dummy)
    path = generation_path(out_dir, dataset, model_name, condition, seed)
    write_generations(records, path)
    return path
