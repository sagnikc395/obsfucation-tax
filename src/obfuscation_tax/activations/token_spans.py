from __future__ import annotations

from typing import Any


def find_answer_span(
    prompt: str,
    completion: str,
    tokenizer: Any,
    aggregation: str = "mean",
) -> tuple[int, int]:
    """Return (start, end) token indices for answer tokens only.
    Prompt tokens are excluded. Uses tokenizer to count prompt tokens.
    Falls back to heuristic if tokenizer is None.
    """
    if tokenizer is not None:
        try:
            prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
            full_ids = tokenizer(prompt + completion, add_special_tokens=False)["input_ids"]
            start = len(prompt_ids)
            end = len(full_ids)
            # guard: ensure at least 1 token
            if end <= start:
                # fallback: last token
                start = max(0, end - 1)
            return (start, end)
        except Exception:
            pass
    # fallback heuristic: approximate tokens as words
    prompt_tokens = len(prompt.split())
    completion_tokens = max(1, len(completion.split()))
    return (prompt_tokens, prompt_tokens + completion_tokens)


def aggregate_hidden_states(
    hidden_states: Any,  # torch.Tensor [seq_len, hidden_dim] or [batch, seq, dim]
    span: tuple[int, int],
    method: str = "mean",
):
    try:
        import torch

        if isinstance(hidden_states, torch.Tensor):
            # assume [seq, dim] or [batch, seq, dim] -> take first batch
            if hidden_states.dim() == 3:
                hidden_states = hidden_states[0]
            sliced = hidden_states[span[0] : span[1]]
            if sliced.shape[0] == 0:
                sliced = hidden_states[-1:]
            if method == "mean":
                return sliced.mean(dim=0)
            elif method == "last":
                return sliced[-1]
            elif method == "max":
                return sliced.max(dim=0).values
            else:
                return sliced.mean(dim=0)
    except ImportError:
        pass
    # numpy fallback
    import numpy as np

    arr = hidden_states  # type: ignore
    sliced = arr[span[0] : span[1]]
    if method == "mean":
        return sliced.mean(axis=0)
    elif method == "last":
        return sliced[-1]
    return sliced.mean(axis=0)
