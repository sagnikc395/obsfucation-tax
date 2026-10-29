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

from .config import LAYERS, MAX_TOP2_POS, POOLINGS

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


def build_chat_prompt(tok, messages):
    kw = {"enable_thinking": False} if "think" in (tok.chat_template or "") else {}
    return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, **kw)


def build_prompt(tok, system, user):
    return build_chat_prompt(tok, [{"role": "system", "content": system},
                                   {"role": "user", "content": user}])


def assert_thinking_disabled(tok):
    """Returns the rendered probe prompt, so a notebook can print its tail."""
    p = build_prompt(tok, "sys", "user")
    if "think" in (tok.chat_template or ""):
        assert "<think>" in p and "</think>" in p, (
            "thinking was not disabled: the prompt ends mid-<think>, so the model will "
            "reason instead of answering and the features will be reasoning tokens"
        )
    return p


def hidden_states(out):
    hs = getattr(out, "hidden_states", None)
    if hs is None:
        hs = out.language_model_outputs.hidden_states   # some VLM wrappers nest it
    return hs


def trim_answer(gen_ids, n_prompt, tok):
    """The generated ids with everything from the first EOS onwards dropped. Falls back
    to one token, because an empty answer breaks pooling."""
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
                      layers=LAYERS, poolings=POOLINGS, max_top2_pos=MAX_TOP2_POS):
    """Generate, then take features from a forward pass over the realised sequence.

    Returns (text, pooled, top2, n_answer) where `pooled[pooling][layer]` is a numpy
    vector over ANSWER TOKENS ONLY, never the prompt, and `top2` is the top-2 predicted
    ids at each answer position (logits at p predict token p+1).
    """
    prompt = build_prompt(tok, system, user)
    text, seq, n_prompt, n_answer = generate(model, tok, prompt, max_new_tokens)

    out = model(seq, output_hidden_states=True)
    hs = hidden_states(out)
    assert len(hs) == n_layers + 1, f"expected {n_layers + 1} hidden states, got {len(hs)}"

    pooled = {p: {} for p in poolings}
    for L in layers:
        a = hs[L + 1][0, n_prompt:].float()
        for p in poolings:
            pooled[p][L] = pool_one(a, p).cpu().numpy()

    logits = out.logits[0, n_prompt - 1 : -1][:max_top2_pos]
    top2 = torch.topk(logits.float(), 2, dim=-1).indices.cpu().numpy().astype(np.int32)

    del out, hs
    return text, pooled, top2, n_answer
