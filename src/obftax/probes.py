"""Fitting the linear probe, and the split it is fitted under.

The label is the one thing in the project that is easy to get wrong, so it lives in one
function: label 0 is honest AND correct, label 1 is a successful attack (correct under
the honest prompt, incorrect under the sandbagging prompt on the same problem). A probe
fitted on anything else can win by separating the two prompts, or the two accuracy
levels, and its AUROC means nothing.
"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .config import SEED


def build_xy(honest_acts, sandbag_acts, h_correct, attacked):
    """Returns (X, y, q): features, labels, and the problem index each row came from."""
    X = np.r_[honest_acts[h_correct], sandbag_acts[attacked]]
    y = np.r_[np.zeros(h_correct.sum()), np.ones(attacked.sum())]
    q = np.r_[np.where(h_correct)[0], np.where(attacked)[0]]
    return X, y, q


def problem_split(q, seed=SEED, frac=0.5):
    """Split by problem, not by row: one problem can supply both labels, and putting
    those on opposite sides leaks the problem text into the test half."""
    q = np.asarray(q)
    uq = np.random.default_rng(seed).permutation(np.unique(q))
    train = set(uq[: int(len(uq) * frac)].tolist())
    # dtype=bool explicitly: an empty list gives a float64 array, and ~float raises
    tr = np.array([x in train for x in q], dtype=bool)
    return tr, ~tr


def fit_probe(X, y, tr):
    p = make_pipeline(StandardScaler(),
                      LogisticRegression(max_iter=5000, class_weight="balanced", C=1.0))
    return p.fit(X[tr], y[tr])


def probe_direction(probe):
    """Unit-norm direction in raw activation space, with the scaler undone. Step 4 steers
    along these, so they are saved rather than refitted later."""
    sc = probe.named_steps["standardscaler"]
    w = probe.named_steps["logisticregression"].coef_[0] / sc.scale_
    return w / np.linalg.norm(w)


def fit_and_score(X, y, q, seed=SEED):
    """Fit on the train half and score the test half in one call, with the guards that
    stop a one-class split from reporting a number. Returns (probe, info) where info
    carries the masks and the test AUROC, or (None, info) when the split is unusable."""
    info = {"n": int(len(y)), "auroc_test": float("nan"), "auroc_train": float("nan")}
    if len(y) < 20 or y.min() == y.max():
        return None, info
    tr, te = problem_split(q, seed=seed)
    if y[tr].min() == y[tr].max() or y[te].min() == y[te].max():
        return None, info
    probe = fit_probe(X, y, tr)
    info.update(
        tr=tr, te=te,
        scores=probe.decision_function(X),
        auroc_test=float(roc_auc_score(y[te], probe.decision_function(X[te]))),
        auroc_train=float(roc_auc_score(y[tr], probe.decision_function(X[tr]))),
    )
    return probe, info


def fit_from_saved(z, pool, layer, h_correct, attacked, seed=SEED):
    """Refit the probe from a saved `pre_*_acts.npz`, under the same seeded by-problem
    split the preconditions notebook used.

    Steps 3-5 and the mech-interp experiments all need the probe, and all of them must
    use the SAME split, so the test half is still only used once. Refitting from the
    saved activations is how that is kept true without pickling an sklearn object.
    """
    X, y, q = build_xy(z[f"honest_{pool}_L{layer}"], z[f"sandbag_{pool}_L{layer}"],
                       h_correct, attacked)
    probe, info = fit_and_score(X, y, q, seed=seed)
    assert probe is not None, (
        f"could not fit a probe at L{layer}/{pool}: {info['n']} rows, one-sided split"
    )
    info.update(X=X, y=y, q=q)
    return probe, info
