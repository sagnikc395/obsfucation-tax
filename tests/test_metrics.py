import numpy as np
from obfuscation_tax.probes.metrics import compute_auroc, compute_accuracy, compute_auprc, bootstrap_ci
from obfuscation_tax.probes.linear import LinearProbe


def test_auroc_perfect():
    y_true = np.array([0, 0, 1, 1])
    y_score = np.array([0.1, 0.2, 0.8, 0.9])
    assert compute_auroc(y_true, y_score) == 1.0


def test_auroc_random():
    y_true = np.array([0, 0, 1, 1])
    y_score = np.array([0.5, 0.5, 0.5, 0.5])
    assert compute_auroc(y_true, y_score) == 0.5


def test_accuracy():
    y_true = np.array([0, 1, 1, 0])
    y_score = np.array([0.1, 0.9, 0.8, 0.2])
    assert compute_accuracy(y_true, y_score) == 1.0


def test_bootstrap():
    y_true = np.array([0, 0, 1, 1, 0, 1])
    y_score = np.array([0.1, 0.2, 0.8, 0.9, 0.3, 0.7])
    mean, lo, hi = bootstrap_ci(y_true, y_score, compute_auroc, n_bootstrap=100, seed=0)
    assert 0 <= lo <= hi <= 1.0
    assert 0 <= mean <= 1.0


def test_failed_attack_filtering_logic():
    from obfuscation_tax.data.schemas import GenerationRecord

    h = GenerationRecord("id1", "d", "train", "honest", 0, "t1", "q", "A", "A", "A", True, "m", None, {})
    s = GenerationRecord("id1", "d", "train", "sandbag_r0", 0, "t2", "q", "B", "B", "A", False, "m", None, {})
    h2 = GenerationRecord("id2", "d", "train", "honest", 0, "t1", "q", "B", "B", "A", False, "m", None, {})
    s2 = GenerationRecord("id2", "d", "train", "sandbag_r0", 0, "t2", "q", "B", "B", "A", False, "m", None, {})

    from obfuscation_tax.probes.dataset import filter_successful_attacks

    hk, sk = filter_successful_attacks([h, h2], [s, s2])
    # only id1 has honest_correct and sandbag_incorrect
    assert len(hk) == 1
    assert hk[0].example_id == "id1"
