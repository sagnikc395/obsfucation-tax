from obfuscation_tax.data.splits import create_splits


def test_deterministic():
    ids = [f"id_{i}" for i in range(20)]
    a1 = create_splits(ids, seed=42)
    a2 = create_splits(ids, seed=42)
    assert a1.train_ids == a2.train_ids
    assert a1.val_ids == a2.val_ids
    a3 = create_splits(ids, seed=43)
    assert a1.train_ids != a3.train_ids


def test_no_overlap():
    ids = [f"id_{i}" for i in range(30)]
    art = create_splits(ids, seed=0, train_frac=0.6, val_frac=0.2, test_frac=0.2)
    art.validate_no_overlap()
    all_ids = set(art.train_ids + art.val_ids + art.test_ids)
    assert len(all_ids) == 30


def test_fractions():
    ids = [str(i) for i in range(10)]
    art = create_splits(ids, seed=1, train_frac=0.5, val_frac=0.3, test_frac=0.2)
    assert len(art.train_ids) == 5
    assert len(art.val_ids) == 3
    assert len(art.test_ids) == 2
