"""Where results go, and how the later notebooks read the earlier one's output.

The pipeline is three notebooks that talk to each other only through `results/`:

    pre_<tag>_summary.json       preconditions and controls   (notebook 01)
    pre_<tag>_records.csv        every generation, both prompts
    pre_<tag>_<track>_acts.npz   activations, masks, probe directions
    attack_<tag>_<track>_*       the monitor, the curve, transfer   (notebook 02)

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
        lines.append("nothing there at all -- run notebooks/sandbagging_experiments.ipynb first, "
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
    # Optional. The npz carries every per-problem label the probe is defined against
    # (h_correct, s_correct, attacked), so a run that arrived without its csv can still
    # be attacked -- what is lost is the saved answer TEXT, which only the monitor
    # baseline needs, and which the downstream notebook regenerates instead.
    rec = pd.read_csv(recs) if os.path.exists(recs) else None
    if rec is not None:
        rec = rec[rec.track == track].copy()

    # The summary carries the config the features were produced under. Downstream
    # notebooks have to generate under the same config, and nothing about the filename
    # says whether reasoning was on, so it is returned rather than left on disk.
    spath = f"{pre}_summary.json"
    summary = json.load(open(spath)) if os.path.exists(spath) else None

    return {"base": pre, "dir": d, "z": z, "records": rec,
            "h_correct": z["h_correct"], "attacked": z["attacked"], "summary": summary}


def check_pre_matches(pre, track, thinking=None):
    """Assert the saved run can legitimately be attacked by this one.

    A probe fitted on thinking-on features steered against thinking-off generations is
    not a weaker experiment, it is a different one, and no filename or shape mismatch
    would catch it. Same for a track the run never generated.
    """
    from . import config

    thinking = config.THINKING if thinking is None else thinking
    s = pre["summary"]
    if s is None:
        # The npz alone is enough to refit the probe, so this is allowed -- but the config
        # it was generated under is only recorded in the summary, so say plainly what is
        # no longer being checked rather than implying the run was verified.
        print(f"WARNING: no pre_<tag>_summary.json next to {pre['base']}_{track}_acts.npz.")
        print("  Cannot verify the saved run's reasoning mode, token budget or problem")
        print("  count. If this notebook generates under a different config than the one")
        print("  that produced these features, every column of the table is invalid and")
        print("  nothing downstream will warn you. Upload the summary json (5 KB) to fix.")
        return {"thinking": None, "n": None, "max_new_tokens": None}
    cfg = s.get("config", {})

    assert track in cfg.get("tracks", {}), (
        f"{track!r} is not in the saved run; it generated {sorted(cfg.get('tracks', {}))}. "
        "The npz for another track cannot stand in: the problems differ."
    )

    saved = bool(cfg.get("thinking"))
    assert saved == bool(thinking), (
        f"the saved run had thinking={saved} but this notebook is set to "
        f"thinking={bool(thinking)}. The probe would be fitted on one kind of answer "
        "token and steered against another. Set obftax.config.THINKING to "
        f"{saved} here, or refit from a run that matches."
    )
    return {"thinking": saved, "n": cfg["tracks"][track]["n"],
            "max_new_tokens": cfg["tracks"][track]["max_new_tokens"]}


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


# every key that is not a (pooling, layer) feature block, and so is always kept
_SMALL_KEYS = ("h_correct", "s_correct", "attacked", "attacked_clean", "held",
               "probe_scores", "probe_q", "probe_y", "probe_train_mask")


def slim_pre(src, dst, poolings=("mean",), layers=(20, 28), verbose=True):
    """Copy a `pre_*_acts.npz` keeping only the feature blocks a downstream notebook reads.

    The full npz is three poolings by five layers by two conditions, and a notebook that
    attacks one layer and transfers to one other touches four of those thirty blocks. The
    rest is ~50 MB of arrays nothing downstream opens, which is the difference between a
    file that uploads to a Colab runtime and one that does not.

    Labels, probe directions and the saved split are all tiny and are kept whatever is
    asked for, so the slim file still reproduces the same probe on the same split.
    """
    want = {f"{cond}_{p}_L{L}" for cond in ("honest", "sandbag")
            for p in poolings for L in layers}
    with np.load(src) as z:
        missing = sorted(want - set(z.files))
        assert not missing, (
            f"{src} has no {', '.join(missing)}. It was written with different poolings "
            f"or layers than {poolings}/{layers} ask for."
        )
        keep = {k: z[k] for k in z.files
                if k in want or k in _SMALL_KEYS or k.startswith("probe_dir_")}
        save_acts(dst, keep)

    if verbose:
        a, b = os.path.getsize(src), os.path.getsize(dst)
        print(f"{len(keep)}/{len(z.files)} arrays, {a / 1e6:.1f} MB -> {b / 1e6:.1f} MB")
        print("kept:", ", ".join(sorted(k for k in keep if k in want)))
    return dst


def _on_colab():
    return os.path.isdir("/content")


def ensure_pre(track, tag=TAG, results=RESULTS, interactive=True):
    """Return the directory holding this run's npz, prompting for an upload if it is not
    there yet.

    `results/` does not survive a fresh clone, so on Colab the activations always have to
    arrive by hand. This opens the file picker in place of failing, accepts the npz on its
    own, and re-checks by filename afterwards -- an upload under the wrong name is the
    usual mistake and looks identical to no upload at all.
    """
    d = find_pre(track, tag=tag, results=results)
    if d is not None:
        return d

    assert interactive and _on_colab(), _pre_not_found(track, tag, results)

    print(f"{results}/ has no pre_{tag}_{track}_acts.npz yet.")
    print(f"Upload pre_{tag}_{track}_acts.npz now.")
    print(f"Bring pre_{tag}_summary.json too if you have it: without it the saved run's")
    print("reasoning mode and token budget cannot be checked against this notebook.")
    print(f"pre_{tag}_records.csv is optional; without it the monitor baseline is")
    print("regenerated instead of read off disk.")

    from google.colab import files   # Colab-only, so imported where it is used

    got = files.upload()
    os.makedirs(results, exist_ok=True)
    for name, data in got.items():
        dst = os.path.join(results, os.path.basename(name))
        with open(dst, "wb") as f:
            f.write(data)
        print(f"saved {dst} ({len(data) / 1e6:.1f} MB)")

    d = find_pre(track, tag=tag, results=results)
    assert d is not None, (
        _pre_not_found(track, tag, results)
        + f"\n\nreceived: {', '.join(sorted(got)) or '(nothing)'}"
        + f"\nthe filename has to be exactly pre_{tag}_{track}_acts.npz, so rename it "
        "or set PRE_TAG and TRACK to match what you uploaded."
    )
    return d
