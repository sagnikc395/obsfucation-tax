"""Loading the model, building prompts, generating, and pooling answer-token features.

Two Qwen3.5 specifics that would silently corrupt the features if missed:

  * It reasons by default. Without `enable_thinking=False` the template ends mid-<think>,
    the answer budget is spent reasoning, and the "answer tokens" the probe reads are
    reasoning tokens. `assert_thinking_disabled` is the check, as an assert.
  * It is a vision-language checkpoint, so the layer count lives in
    `config.text_config` and the hidden states can arrive nested.
"""

import numpy as np
import torch
from transformers import (
    AutoModel,
    AutoModelForCausalLM,
    AutoModelForImageTextToText,
)

from . import config
from .config import LAYERS, MAX_TOP2_POS, POOLINGS

THINK_OPEN, THINK_CLOSE = "<think>", "</think>"

_DECODER_PATHS = (
    "model.language_model.layers",
    "model.model.language_model.layers",
    "model.model.layers",
    "model.layers",
    "language_model.model.layers",
)


def device():
    if torch.cuda.is_available():
        return "cuda"
    return "mps" if torch.backends.mps.is_available() else "cpu"


def load_model(name, dev=None, verbose=True):
    """Try the auto classes in turn: the checkpoint is a VLM, so which one works
    depends on the transformers version."""
    dev = dev or device()
    dtype = torch.bfloat16 if (dev == "cuda" and torch.cuda.is_bf16_supported()) else torch.float16
    for cls in (AutoModelForCausalLM, AutoModelForImageTextToText, AutoModel):
        try:
            model = cls.from_pretrained(name, dtype=dtype, device_map=dev)
            if verbose:
                print(f"loaded {name} with {cls.__name__} ({dtype})")
            return model.eval()
        except Exception as e:
            if verbose:
                print(f"  {cls.__name__} failed: {str(e)[:100]}")
    raise RuntimeError(f"could not load {name}")


def text_config(model):
    """The VLM wrapper keeps num_hidden_layers and hidden_size one level down."""
    return getattr(model.config, "text_config", model.config)


def decoder_layers(model, n_layers=None):
    """The module list the hooks attach to. The path differs between the CausalLM and
    the VLM wrappers, so it is found by matching the expected length."""
    n_layers = n_layers or text_config(model).num_hidden_layers
    for path in _DECODER_PATHS:
        obj = model
        try:
            for part in path.split("."):
                obj = getattr(obj, part)
        except AttributeError:
            continue
        if hasattr(obj, "__len__") and len(obj) == n_layers:
            return obj
    raise RuntimeError("could not find the decoder layer list; print(model) and add the path")


def build_chat_prompt(tok, messages, thinking=None):
    """`thinking` defaults to config.THINKING. Templates without a think block ignore it."""
    thinking = config.THINKING if thinking is None else thinking
    kw = {"enable_thinking": bool(thinking)} if "think" in (tok.chat_template or "") else {}
    return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, **kw)


def build_prompt(tok, system, user, thinking=None):
    return build_chat_prompt(tok, [{"role": "system", "content": system},
                                   {"role": "user", "content": user}], thinking=thinking)


def check_thinking(tok, thinking=None):
    """Assert the template is in the state we think it is, and return the rendered prompt.

    With thinking off the template must emit a closed, empty think block; a prompt that
    ends mid-`<think>` means the model will reason instead of answering and the "answer
    tokens" the probe reads will be reasoning tokens. With thinking on the block must NOT
    be pre-closed, or the model has been told to skip reasoning.
    """
    thinking = config.THINKING if thinking is None else thinking
    p = build_prompt(tok, "sys", "user", thinking=thinking)
    if "think" in (tok.chat_template or ""):
        closed = THINK_CLOSE in p
        if thinking:
            assert not closed, (
                "thinking is meant to be ON, but the template pre-closes the think block, "
                "so the model will not reason"
            )
        else:
            assert "<think>" in p and closed, (
                "thinking was not disabled: the prompt ends mid-<think>, so the model will "
                "reason instead of answering and the features will be reasoning tokens"
            )
    return p


def answer_start(new_ids, tok):
    """Index into `new_ids` where the answer begins, just past the last `</think>`.

    Returns (start, ok). `ok` is False only when the span opened a trace that never
    closed inside the token budget, which means the model never answered: a failed
    generation rather than a wrong answer, counted separately by the run. A span with no
    trace at all is the whole answer, so `ok` is True and `start` is 0.

    Two strategies, because whether `</think>` is one token is a tokenizer detail. The id
    lookup is exact when the token exists; otherwise prefixes are decoded until the last
    occurrence is passed, which is a few hundred cheap decodes at most.
    """
    if not new_ids:
        return 0, False

    tid = tok.convert_tokens_to_ids(THINK_CLOSE)
    unk = getattr(tok, "unk_token_id", None)
    if isinstance(tid, int) and tid >= 0 and tid != unk and tid in new_ids:
        return len(new_ids) - new_ids[::-1].index(tid), True

    whole = tok.decode(new_ids, skip_special_tokens=False)
    total = whole.count(THINK_CLOSE)
    if total == 0:
        # no closing tag: an unclosed trace is a failure, no trace at all is just an answer
        return 0, THINK_OPEN not in whole
    for k in range(1, len(new_ids) + 1):
        if tok.decode(new_ids[:k], skip_special_tokens=False).count(THINK_CLOSE) == total:
            return k, True
    return 0, True


def split_generation(new_ids, tok):
    """Split a generated span into its reasoning trace and its answer.

    Returns a dict with the answer ids and text, the trace text, the length of each part,
    and `closed`: whether an answer was actually produced. With thinking off the whole
    span is the answer.

    When the trace never closed, or closed with nothing after it, there is no answer. The
    text comes back empty so scoring marks the row wrong, and one token is kept so pooling
    stays defined; `closed` is False and the run reports the rate separately. Those rows
    are a budget failure, not an attack.
    """
    start, closed = (answer_start(new_ids, tok) if config.THINKING else (0, True))
    answer_ids = new_ids[start:] if closed else []

    if not answer_ids:
        return {"answer_ids": new_ids[-1:] or [0], "text": "",
                "trace_text": tok.decode(new_ids, skip_special_tokens=True),
                "n_answer": 0, "n_trace": len(new_ids), "closed": False}

    return {
        "answer_ids": answer_ids,
        "text": tok.decode(answer_ids, skip_special_tokens=True),
        "trace_text": tok.decode(new_ids[:start], skip_special_tokens=True),
        "n_answer": len(answer_ids),
        "n_trace": start,
        "closed": True,
    }


def hidden_states(out):
    hs = getattr(out, "hidden_states", None)
    if hs is None:
        hs = out.language_model_outputs.hidden_states   # some VLM wrappers nest it
    return hs


def trim_answer(gen_ids, n_prompt, tok):
    """The generated ids with everything from the first EOS onwards dropped. Falls back
    to one token, because an empty generation breaks pooling."""
    new = gen_ids[n_prompt:].tolist()
    if tok.eos_token_id in new:
        new = new[: new.index(tok.eos_token_id)]
    if not new:
        new = gen_ids[n_prompt : n_prompt + 1].tolist()
    return new


@torch.no_grad()
def generate(model, tok, prompt, max_new_tokens, hooks=(), layers_mod=None):
    """Greedy generation, optionally under forward hooks.

    `hooks` is passed straight to obftax.hooks.attach, with `layers_mod` when the
    targets are layer indices rather than modules.

    Returns (text, seq, n_prompt, n_answer). `seq` is prompt+answer as one batch of ids:
    re-tokenizing prompt+answer can move the boundary by a token and leak prompt
    positions into the features, so the follow-up forward pass uses this.
    """
    from .hooks import attach

    enc = tok(prompt, return_tensors="pt").to(model.device)
    n_prompt = enc["input_ids"].shape[1]
    with attach(hooks, layers_mod):
        gen = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                             pad_token_id=tok.eos_token_id)[0]
    new = trim_answer(gen, n_prompt, tok)
    seq = torch.cat([gen[:n_prompt], torch.tensor(new, device=gen.device)]).unsqueeze(0)
    text = tok.decode(torch.tensor(new), skip_special_tokens=True)
    return text, seq, n_prompt, len(new)


def pool_one(a, how):
    """`a` is [n_answer_tokens, d_model]."""
    if how == "mean":
        return a.mean(0)
    if how == "last":
        return a[-1]
    if how == "last32":
        return a[-32:].mean(0)
    raise ValueError(f"unknown pooling {how!r}")


@torch.no_grad()
def generate_and_pool(model, tok, system, user, max_new_tokens, n_layers,
                      layers=LAYERS, poolings=POOLINGS, max_top2_pos=MAX_TOP2_POS,
                      thinking=None):
    """Generate, then take features from a forward pass over the realised sequence.

    Returns (text, pooled, top2, info).

    `text` is the answer with any reasoning trace stripped, so scoring never sees the
    trace. `pooled[pooling][layer]` is a numpy vector over ANSWER TOKENS ONLY: never the
    prompt, and never the trace. `top2` is the top-2 predicted ids at each answer
    position. `info` carries n_answer, n_trace, closed and the trace text, because trace
    length differs by condition and has to be checked rather than assumed.
    """
    prompt = build_prompt(tok, system, user, thinking=thinking)
    enc = tok(prompt, return_tensors="pt").to(model.device)
    n_prompt = enc["input_ids"].shape[1]
    gen = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                         pad_token_id=tok.eos_token_id)[0]
    new = trim_answer(gen, n_prompt, tok)

    part = split_generation(new, tok)
    # The forward pass covers prompt + trace + answer, since the answer was produced in
    # that context. Features are then taken from the answer positions only.
    seq = torch.cat([gen[:n_prompt], torch.tensor(new, device=gen.device)]).unsqueeze(0)
    a0 = n_prompt + (len(new) - len(part["answer_ids"]))

    out = model(seq, output_hidden_states=True)
    hs = hidden_states(out)
    assert len(hs) == n_layers + 1, f"expected {n_layers + 1} hidden states, got {len(hs)}"

    pooled = {p: {} for p in poolings}
    for L in layers:
        a = hs[L + 1][0, a0:].float()
        for p in poolings:
            pooled[p][L] = pool_one(a, p).cpu().numpy()

    logits = out.logits[0, a0 - 1 : -1][:max_top2_pos]
    top2 = torch.topk(logits.float(), 2, dim=-1).indices.cpu().numpy().astype(np.int32)

    del out, hs
    return part["text"], pooled, top2, {k: part[k] for k in
                                        ("n_answer", "n_trace", "closed", "trace_text")}
