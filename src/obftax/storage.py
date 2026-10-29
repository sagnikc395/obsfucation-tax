"""Where results go, and how the later notebooks read the earlier one's output.

The pipeline is three notebooks that talk to each other only through `results/`:

    pre_<tag>_summary.json       preconditions and controls   (notebook 01)
    pre_<tag>_records.csv        every generation, both prompts
    pre_<tag>_<track>_acts.npz   activations, masks, probe directions
    attack_<tag>_<track>_*       the monitor, the curve, transfer   (notebook 02)
    mech_<tag>_<track>_*         the mech-interp experiments        (notebook 03)

Nothing downstream recomputes a number that is already in one of these files.
"""

import json
import os
import shutil

import numpy as np

from .config import RESULTS, TAG


def base_path(prefix, tag=TAG, track=None, results=RESULTS):
    os.makedirs(results, exist_ok=True)
    name = f"{prefix}_{tag}" + (f"_{track}" if track else "")
    return os.path.join(results, name)


def save_summary(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    return path


def load_summary(path):
    with open(path) as f:
        return json.load(f)


def load_pre(track, tag=TAG, results=RESULTS):
    """The preconditions notebook's output for one track: the npz, the records frame,
    and the two masks everything downstream is defined against."""
    import pandas as pd

    pre = base_path("pre", tag=tag, results=results)
    npz = f"{pre}_{track}_acts.npz"
    assert os.path.exists(npz), f"missing {npz} -- run notebooks/01_preconditions.ipynb"
    z = np.load(npz)
    rec = pd.read_csv(f"{pre}_records.csv")
    return {"base": pre, "z": z, "records": rec[rec.track == track].copy(),
            "h_correct": z["h_correct"], "attacked": z["attacked"]}


def save_acts(path, arrays):
    np.savez_compressed(path, **arrays)
    return path


def pad_ragged(seqs, width=None, fill=-1, dtype=np.int32):
    """Top-2 id arrays differ in length across examples (answers differ in length), and
    npz needs one rectangular array."""
    width = width or max(x.shape[0] for x in seqs)
    out = np.full((len(seqs), width) + seqs[0].shape[1:], fill, dtype=dtype)
    for i, x in enumerate(seqs):
        out[i, : x.shape[0]] = x
    return out


def zip_results(name, results=RESULTS, download=True):
    """Zip `results/` and, on Colab, offer it as a download. A long mbpp run is
    expensive enough that losing it to a disconnected runtime is worth one cell."""
    zip_dir = "/content" if os.path.isdir("/content") else "."   # /content is Colab-only
    path = shutil.make_archive(os.path.join(zip_dir, name), "zip", results)
    print(path, round(os.path.getsize(path) / 1e6, 1), "MB")
    if download:
        try:
            from google.colab import files
            files.download(path)
        except Exception as e:
            print("not in Colab, or download blocked:", e)
    return path
