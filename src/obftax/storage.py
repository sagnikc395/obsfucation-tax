"""Where results go, and how the later notebooks read the earlier one's output.

The pipeline is three notebooks that talk to each other only through `results/`:

    pre_<tag>_summary.json       preconditions and controls   (notebook 01)
    pre_<tag>_records.csv        every generation, both prompts
    pre_<tag>_<track>_acts.npz   activations, masks, probe directions
    attack_<tag>_<track>_*       the monitor, the curve, transfer   (notebook 02)
    mech_<tag>_<track>_*         the mech-interp experiments        (notebook 03)

Nothing downstream recomputes a number that is already in one of these files.
"""

import glob
import json
import os
import shutil
import zipfile

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


def find_pre(track, tag=TAG, results=RESULTS, verbose=True):
    """Locate the directory holding `pre_<tag>_<track>_acts.npz`.

    A run does not always leave its files flat in `results/`. The notebooks zip their
    output so a Colab session can be reconnected or the files moved to another machine,
    so by the time a later notebook looks for them they may be one directory down, or
    still inside the zip. All three layouts are accepted, and a zip is unpacked once.
    """
    name = f"pre_{tag}_{track}_acts.npz"

    if os.path.exists(os.path.join(results, name)):
        return results

    for d in sorted(glob.glob(os.path.join(results, "*", ""))):
        if os.path.exists(os.path.join(d, name)):
            if verbose:
                print(f"found {name} in {d}")
            return os.path.normpath(d)

    for zp in sorted(glob.glob(os.path.join(results, "*.zip"))):
        try:
            with zipfile.ZipFile(zp) as zf:
                if not any(os.path.basename(m) == name for m in zf.namelist()):
                    continue
                out = os.path.join(
                    results, os.path.splitext(os.path.basename(zp))[0] + "_extracted")
                zf.extractall(out)
        except zipfile.BadZipFile:
            continue
        for root, _, files in os.walk(out):
            if name in files:
                if verbose:
                    print(f"unpacked {zp} -> {root}")
                return root

    return None


def _pre_not_found(track, tag, results):
    """The old message told you to run notebook 01 even when you just had. Say what is
    actually on disk instead."""
    lines = [f"no pre_{tag}_{track}_acts.npz under {results}/"]
    seen = sorted(
        {os.path.basename(f) for f in glob.glob(os.path.join(results, "**", "pre_*_acts.npz"),
                                                recursive=True)}
        | {os.path.basename(f) for f in glob.glob(os.path.join(results, "*.zip"))})
    if seen:
        lines.append("found instead: " + ", ".join(seen))
        tags = sorted({b[len("pre_"):-len("_acts.npz")] for b in seen if b.startswith("pre_")
                       and b.endswith("_acts.npz")})
        if tags:
            lines.append("those are <tag>_<track> pairs, so set PRE_TAG and TRACK to match "
                         "one of: " + ", ".join(tags))
    else:
        lines.append("nothing there at all -- run notebooks/01_preconditions.ipynb first, "
                     "or upload its zip into results/")
    return "\n".join(lines)


def load_pre(track, tag=TAG, results=RESULTS):
    """The preconditions notebook's output for one track: the npz, the records frame,
    and the two masks everything downstream is defined against."""
    import pandas as pd

    d = find_pre(track, tag=tag, results=results)
    assert d is not None, _pre_not_found(track, tag, results)

    pre = os.path.join(d, f"pre_{tag}")
    z = np.load(f"{pre}_{track}_acts.npz")
    recs = f"{pre}_records.csv"
    assert os.path.exists(recs), (
        f"found the activations but not {recs}. Both come out of the same run, so this is "
        "a half-copied result rather than a missing one."
    )
    rec = pd.read_csv(recs)
    return {"base": pre, "dir": d, "z": z, "records": rec[rec.track == track].copy(),
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
