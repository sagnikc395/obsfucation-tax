"""Dataset loaders. Each returns problems in one shape, so everything downstream is
track-agnostic:

    {"track", "id", "kind", "user", ...}

`kind` is "literal" (one Python value, exact match) or "program" (a function, scored by
running the official tests). A literal problem carries "expected"; a program problem
carries "prefix" and "test_src".
"""

import random

from datasets import load_dataset


def load_cruxeval(n, seed):
    ds = load_dataset("cruxeval-org/cruxeval", split="test")
    out = []
    for i in random.Random(seed).sample(range(len(ds)), min(n, len(ds))):
        r = ds[i]
        out.append({
            "track": "cruxeval", "id": r["id"], "kind": "literal",
            "user": f"{r['code']}\n\nassert f({r['input']}) == ??\n\nWhat value replaces ??",
            "expected": r["output"],
        })
    return out


def load_mbpp(n, seed):
    ds = load_dataset("google-research-datasets/mbpp", "full", split="test")
    out = []
    for i in random.Random(seed).sample(range(len(ds)), min(n, len(ds))):
        r = ds[i]
        out.append({
            "track": "mbpp", "id": int(r["task_id"]), "kind": "program",
            "user": f"{r['text']}\n\nYour function must satisfy this test:\n"
                    f"{r['test_list'][0]}\n\nWrite the complete function.",
            "prefix": (r["test_setup_code"] or "").strip(),
            "test_src": "\n".join(r["test_list"]),
        })
    return out


def load_humaneval(n, seed):
    ds = load_dataset("openai/openai_humaneval", split="test")
    out = []
    for i in random.Random(seed).sample(range(len(ds)), min(n, len(ds))):
        r = ds[i]
        out.append({
            "track": "humaneval", "id": r["task_id"], "kind": "program",
            "user": "Complete this function. Keep the signature exactly as given.\n\n"
                    f"{r['prompt']}",
            "prefix": "",
            "test_src": r["test"] + f"\ncheck({r['entry_point']})\n",
        })
    return out


def _refusal_loader(track):
    """Imported lazily: refusal.py pulls in the behaviour lists and the marker table, and
    the code tracks have no reason to touch either."""
    def load(n, seed, **kw):
        from .refusal import load_refusal_track
        return load_refusal_track(track, n, seed, **kw)
    return load


LOADERS = {"cruxeval": load_cruxeval, "mbpp": load_mbpp, "humaneval": load_humaneval,
           "advbench": _refusal_loader("advbench"),
           "harmbench": _refusal_loader("harmbench")}


def load_track(track, n, seed, **kw):
    """The loaders are keyed by track so a notebook can take the track from a config
    cell rather than naming a function. `**kw` reaches the refusal loaders, which accept
    `local_csv` for the official behaviour files."""
    assert track in LOADERS, f"unknown track {track!r}; have {sorted(LOADERS)}"
    return LOADERS[track](n, seed, **kw)
