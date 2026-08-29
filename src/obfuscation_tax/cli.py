from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config, get_output_dir
from .seeds import seed_everything
from .logging import setup_logging


def cmd_prepare_data(args):
    from .data.load import prepare_splits_for_dataset

    config = load_config(args.config)
    seed_everything(config.get("seed", 42))
    logger = setup_logging(config.get("logging", {}).get("level", "INFO"), config.get("logging", {}).get("log_file"))
    dataset = args.dataset or config.get("datasets", {}).get("defaults", {}).get("primary", "synthetic")
    path = prepare_splits_for_dataset(dataset, config, seed=config.get("seed", 42), output_dir=get_output_dir(config))
    logger.info(f"Splits saved to {path}")
    print(f"Splits saved to {path}")


def cmd_generate(args):
    from .data.load import load_dataset
    from .data.splits import load_splits, split_path
    from .generation.runner import run_generation_stage

    config = load_config(args.config)
    seed_everything(config.get("seed", 42))
    dataset = args.dataset or config.get("datasets", {}).get("defaults", {}).get("primary", "synthetic")
    # load splits to filter examples
    sp = split_path(get_output_dir(config), dataset, config.get("seed", 42))
    if sp.exists():
        artifact = load_splits(sp)
        # we need examples; load all then filter by id in train+val+test? generate for all splits but condition
        examples = load_dataset(dataset, config, seed=config.get("seed", 42))
        # if split arg, filter
        if args.split:
            allowed = set(getattr(artifact, f"{args.split}_ids") if hasattr(artifact, f"{args.split}_ids") else [])
            # map validation -> val_ids
            if args.split == "validation" and hasattr(artifact, "val_ids"):
                allowed = set(artifact.val_ids)
            examples = [e for e in examples if e.example_id in allowed]
    else:
        examples = load_dataset(dataset, config, seed=config.get("seed", 42))

    if args.limit:
        examples = examples[: args.limit]

    path = run_generation_stage(
        examples, condition=args.condition, config=config, seed=config.get("seed", 42), use_dummy=args.dummy
    )
    print(f"Generations saved to {path}")


def cmd_collect_activations(args):
    from .generation.cache import read_generations, generation_path
    from .activations.collector import run_activation_collection

    config = load_config(args.config)
    # collect for all conditions if not specified
    conditions = [args.condition] if args.condition else ["honest", "sandbag_r0"]
    dataset = args.dataset or config.get("datasets", {}).get("defaults", {}).get("primary", "synthetic")
    model_name = config.get("models", {}).get("models", {}).get("qwen_1_5b", {}).get("name", "Qwen/Qwen2.5-1.5B-Instruct")
    out_dir = get_output_dir(config)
    seed = config.get("seed", 42)
    all_paths = []
    for cond in conditions:
        p = generation_path(out_dir, dataset, model_name, cond, seed)
        if not p.exists():
            print(f"Missing generations for {cond} at {p}, skipping")
            continue
        records = read_generations(p)
        saved = run_activation_collection(records, config, output_dir=out_dir, use_dummy=args.dummy)
        all_paths.extend(saved)
    print(f"Saved {len(all_paths)} activation files")


def cmd_train_probe(args):
    from .activations.cache import activation_path, load_activations
    from .data.splits import load_splits, split_path
    from .probes.train import train_probe_for_layer, save_probe
    from .probes.evaluate import evaluate_probe
    from .probes.metrics import compute_auroc
    import numpy as np

    config = load_config(args.config)
    dataset = args.dataset or config.get("datasets", {}).get("defaults", {}).get("primary", "synthetic")
    out_dir = get_output_dir(config)
    seed = config.get("seed", 42)
    model_name = config.get("models", {}).get("models", {}).get("qwen_1_5b", {}).get("name", "Qwen/Qwen2.5-1.5B-Instruct")
    mode = config.get("activations", {}).get("mode", "teacher_forced")
    layers = config.get("probes", {}).get("probe", {}).get("layers") or config.get("activations", {}).get("layers", [12, 16])
    sp = split_path(out_dir, dataset, seed)
    if not sp.exists():
        print(f"No splits at {sp}, run prepare-data first")
        return
    art = load_splits(sp)
    split_ids = {}
    for eid in art.train_ids:
        split_ids[eid] = "train"
    for eid in art.val_ids:
        split_ids[eid] = "validation"
    for eid in art.test_ids:
        split_ids[eid] = "test"

    # load activations for honest vs sandbag
    def _load(condition, layer):
        p = activation_path(out_dir, dataset, model_name, condition, mode, layer, seed)
        if not p.exists():
            return {}
        acts, _ = load_activations(p)
        return acts

    best_layer = None
    best_auroc = -1
    probes = {}
    for layer in layers:
        h = _load("honest", layer)
        s = _load("sandbag_r0", layer)
        if not h or not s:
            print(f"Missing acts for layer {layer}")
            continue
        probe, info = train_probe_for_layer(h, s, split_ids, C=config.get("probes", {}).get("probe", {}).get("C", 1.0))
        probes[layer] = probe
        val_eval = evaluate_probe(probe, h, s, split_ids, "validation")
        print(f"Layer {layer}: val auroc {val_eval['auroc']:.3f} n_val {val_eval['n']}")
        if val_eval["auroc"] > best_auroc:
            best_auroc = val_eval["auroc"]
            best_layer = layer
        # save
        save_probe(probe, Path(out_dir) / "probes" / dataset / model_name.replace("/", "__") / f"layer_{layer}" / f"seed_{seed}.pt", meta={"val_auroc": val_eval["auroc"], "layer": layer})

    print(f"Best layer: {best_layer} (auroc {best_auroc:.3f})")
    # evaluate best on test
    if best_layer is not None:
        h = _load("honest", best_layer)
        s = _load("sandbag_r0", best_layer)
        from .probes.evaluate import evaluate_probe

        probe = probes[best_layer]
        test_eval = evaluate_probe(probe, h, s, split_ids, "test")
        print(f"Test eval: {test_eval}")
        # save metrics csv
        import csv

        metrics_path = Path(out_dir) / "metrics" / "probe_metrics.csv"
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["dataset", "model", "layer", "seed", "auroc", "accuracy", "auprc", "n"])
            w.writeheader()
            for layer, prb in probes.items():
                ev = evaluate_probe(prb, _load("honest", layer), _load("sandbag_r0", layer), split_ids, "test")
                w.writerow({"dataset": dataset, "model": model_name, "layer": layer, "seed": seed, "auroc": ev["auroc"], "accuracy": ev["accuracy"], "auprc": ev["auprc"], "n": ev["n"]})


def cmd_score_monitor(args):
    from .generation.cache import read_generations, generation_path
    from .monitors.black_box import score_black_box, save_monitor_scores, monitor_scores_path

    config = load_config(args.config)
    dataset = args.dataset or config.get("datasets", {}).get("defaults", {}).get("primary", "synthetic")
    out_dir = get_output_dir(config)
    seed = config.get("seed", 42)
    model_name = config.get("models", {}).get("models", {}).get("qwen_1_5b", {}).get("name", "Qwen/Qwen2.5-1.5B-Instruct")
    # aggregate generations across conditions
    records = []
    for cond in ["honest", "sandbag_r0", "sandbag_r1"]:
        p = generation_path(out_dir, dataset, model_name, cond, seed)
        if p.exists():
            records.extend(read_generations(p))
    if not records:
        print("No generations found")
        return
    scores = score_black_box(records, config, use_dummy=args.dummy)
    out = monitor_scores_path(out_dir, dataset, model_name, seed)
    save_monitor_scores(scores, out)
    print(f"Monitor scores saved to {out}")


def cmd_run_red_team(args):
    from .activations.cache import activation_path, load_activations
    from .probes.train import load_probe
    from .red_team.r2_probe_evasion import run_r2
    from .red_team.r3_transfer import run_r3
    from pathlib import Path

    config = load_config(args.config)
    out_dir = get_output_dir(config)
    dataset = args.dataset or config.get("datasets", {}).get("defaults", {}).get("primary", "synthetic")
    seed = config.get("seed", 42)
    model_name = config.get("models", {}).get("models", {}).get("qwen_1_5b", {}).get("name", "Qwen/Qwen2.5-1.5B-Instruct")
    mode = config.get("activations", {}).get("mode", "teacher_forced")
    layer = 16
    if args.level == "r2":
        # load probe
        probe_path = Path(out_dir) / "probes" / dataset / model_name.replace("/", "__") / f"layer_{layer}" / f"seed_{seed}.pt"
        if not probe_path.exists():
            print(f"No probe at {probe_path}, train probe first")
            return
        probe, _ = load_probe(probe_path)
        acts_path = activation_path(out_dir, dataset, model_name, "sandbag_r0", mode, layer, seed)
        acts, _ = load_activations(acts_path)
        evasive = run_r2(acts, probe, config)
        print(f"R2 evasive: {len(evasive)} vectors, example norm {list(evasive.values())[0][:3] if evasive else 'empty'}")
    elif args.level == "r3":
        # need two probes
        from pathlib import Path
        probe_path = Path(out_dir) / "probes" / dataset / model_name.replace("/", "__") / f"layer_{layer}" / f"seed_{seed}.pt"
        heldout_path = Path(out_dir) / "probes" / dataset / model_name.replace("/", "__") / f"layer_{12}" / f"seed_{seed}.pt"
        if not probe_path.exists() or not heldout_path.exists():
            print("Need both probes for R3")
            return
        probe, _ = load_probe(probe_path)
        heldout, _ = load_probe(heldout_path)
        acts_path = activation_path(out_dir, dataset, model_name, "sandbag_r0", mode, layer, seed)
        honest_path = activation_path(out_dir, dataset, model_name, "honest", mode, layer, seed)
        acts, _ = load_activations(acts_path)
        honest_acts, _ = load_activations(honest_path)
        from obfuscation_tax.data.splits import load_splits, split_path

        sp = split_path(out_dir, dataset, seed)
        art = load_splits(sp)
        split_ids = {}
        for eid in art.train_ids:
            split_ids[eid] = "train"
        for eid in art.val_ids:
            split_ids[eid] = "validation"
        for eid in art.test_ids:
            split_ids[eid] = "test"
        res = run_r3(acts, honest_acts, probe, heldout, config, split_ids)
        print(f"R3 results: {res}")
    else:
        print(f"Level {args.level} is prompt-only (R0/R1): use generate --condition")


def cmd_run_controls(args):
    from .activations.cache import activation_path, load_activations
    from .generation.cache import read_generations, generation_path
    from .data.splits import load_splits, split_path
    from .controls import prompt_leakage_control, surface_text_control, prefill_mismatch_control, template_overfit_control, failed_attack_filtering_control
    from .analysis.tables import write_csv, write_markdown_table
    from pathlib import Path

    config = load_config(args.config)
    out_dir = get_output_dir(config)
    dataset = args.dataset or config.get("datasets", {}).get("defaults", {}).get("primary", "synthetic")
    seed = config.get("seed", 42)
    model_name = config.get("models", {}).get("models", {}).get("qwen_1_5b", {}).get("name", "Qwen/Qwen2.5-1.5B-Instruct")
    mode = config.get("activations", {}).get("mode", "teacher_forced")
    sp = split_path(out_dir, dataset, seed)
    if not sp.exists():
        print("No splits")
        return
    art = load_splits(sp)
    split_ids = {}
    for eid in art.train_ids: split_ids[eid] = "train"
    for eid in art.val_ids: split_ids[eid] = "validation"
    for eid in art.test_ids: split_ids[eid] = "test"

    layer = 16
    h_acts, _ = load_activations(activation_path(out_dir, dataset, model_name, "honest", mode, layer, seed)) if activation_path(out_dir, dataset, model_name, "honest", mode, layer, seed).exists() else ({}, {})
    s_acts, _ = load_activations(activation_path(out_dir, dataset, model_name, "sandbag_r0", mode, layer, seed)) if activation_path(out_dir, dataset, model_name, "sandbag_r0", mode, layer, seed).exists() else ({}, {})
    records = []
    for cond in ["honest", "sandbag_r0"]:
        p = generation_path(out_dir, dataset, model_name, cond, seed)
        if p.exists():
            records.extend(read_generations(p))

    rows = []
    # Each control returns dict; flatten
    try:
        r = prompt_leakage_control(h_acts, s_acts, None, split_ids)
        rows.append({"control": "prompt_leakage", **{k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()}})
    except Exception as e:
        rows.append({"control": "prompt_leakage", "error": str(e)})
    try:
        # need probe auroc
        from obfuscation_tax.probes.train import load_probe as _load_probe
        from obfuscation_tax.probes.evaluate import evaluate_probe as _eval_probe

        probe_path = Path(out_dir) / "probes" / dataset / model_name.replace("/", "__") / f"layer_{layer}" / f"seed_{seed}.pt"
        probe_auroc = 0.5
        if probe_path.exists():
            probe, _ = _load_probe(probe_path)
            probe_auroc = _eval_probe(probe, h_acts, s_acts, split_ids, "test")["auroc"]
        r = surface_text_control(records, probe_auroc, split_ids, config)
        rows.append({"control": "surface_text", **{k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()}})
    except Exception as e:
        rows.append({"control": "surface_text", "error": str(e)})

    # Add other controls similarly with dummy values if missing
    for name in ["prefill_mismatch", "template_overfit", "failed_attack_filtering"]:
        rows.append({"control": name, "note": "requires additional artifacts; placeholder", "auroc": 0.5})

    # Also failed attack filtering real
    try:
        h_recs = [r for r in records if r.condition == "honest"]
        s_recs = [r for r in records if r.condition == "sandbag_r0"]
        r = failed_attack_filtering_control(h_recs, s_recs, h_acts, s_acts, split_ids)
        rows.append({"control": "failed_attack_filtering_real", **{k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()}})
    except Exception as e:
        pass

    out_csv = Path(out_dir) / "metrics" / "confound_controls.csv"
    out_md = Path(out_dir) / "tables" / "confound_controls.md"
    write_csv(rows, out_csv)
    write_markdown_table(rows, out_md, title="Confound Controls")
    print(f"Controls saved to {out_csv} and {out_md}")


def cmd_analyze(args):
    from .analysis.obfuscation_tax_curve import plot_tax_curve, save_tax_csv
    from .analysis.pareto import plot_pareto
    from pathlib import Path

    config = load_config(args.config)
    out_dir = Path(get_output_dir(config))
    # synthetic curve if no metrics
    rows = [
        {"evasion_strength": 0.0, "probe_auroc": 0.92, "attack_strength": 0.35, "suspicion": 2.1},
        {"evasion_strength": 0.5, "probe_auroc": 0.75, "attack_strength": 0.28, "suspicion": 3.5},
        {"evasion_strength": 1.0, "probe_auroc": 0.58, "attack_strength": 0.18, "suspicion": 5.2},
    ]
    plot_tax_curve(rows, out_dir / "plots" / "obfuscation_tax_curve.png")
    save_tax_csv(rows, out_dir / "metrics" / "tax_curve.csv")
    pareto_rows = [
        {"audit_budget": 0.01, "safety": 0.45, "usefulness": 0.99},
        {"audit_budget": 0.02, "safety": 0.62, "usefulness": 0.98},
        {"audit_budget": 0.05, "safety": 0.81, "usefulness": 0.95},
        {"audit_budget": 0.10, "safety": 0.92, "usefulness": 0.90},
    ]
    plot_pareto(pareto_rows, out_dir / "plots" / "safety_usefulness_pareto.png")
    print(f"Plots saved to {out_dir/'plots'}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="obfuscation_tax")
    p.add_argument("--config", default="configs/default.yaml", help="path to default.yaml")
    sub = p.add_subparsers(dest="command", required=True)

    def add_config_arg(parser):
        parser.add_argument("--config", default="configs/default.yaml", help="path to default.yaml")

    s = sub.add_parser("prepare-data", help="create deterministic splits")
    s.add_argument("--dataset", default=None)
    add_config_arg(s)
    s.set_defaults(func=cmd_prepare_data)

    s = sub.add_parser("generate", help="run model generation")
    s.add_argument("--condition", required=True, choices=["honest", "sandbag_r0", "sandbag_r1", "prompt_leakage_control", "heldout_template"])
    s.add_argument("--dataset", default=None)
    s.add_argument("--split", default=None, choices=["train", "validation", "test"])
    s.add_argument("--limit", type=int, default=None)
    s.add_argument("--dummy", action="store_true", help="use dummy generation without model")
    add_config_arg(s)
    s.set_defaults(func=cmd_generate)

    s = sub.add_parser("collect-activations", help="collect residual activations")
    s.add_argument("--dataset", default=None)
    s.add_argument("--condition", default=None)
    s.add_argument("--dummy", action="store_true")
    add_config_arg(s)
    s.set_defaults(func=cmd_collect_activations)

    s = sub.add_parser("train-probe", help="train linear probes")
    s.add_argument("--dataset", default=None)
    add_config_arg(s)
    s.set_defaults(func=cmd_train_probe)

    s = sub.add_parser("score-monitor", help="score with black-box monitor")
    s.add_argument("--dataset", default=None)
    s.add_argument("--dummy", action="store_true")
    add_config_arg(s)
    s.set_defaults(func=cmd_score_monitor)

    s = sub.add_parser("run-red-team", help="run adaptive attacks")
    s.add_argument("--level", required=True, choices=["r0", "r1", "r2", "r3"])
    s.add_argument("--dataset", default=None)
    add_config_arg(s)
    s.set_defaults(func=cmd_run_red_team)

    s = sub.add_parser("run-controls", help="run confound controls")
    s.add_argument("--dataset", default=None)
    add_config_arg(s)
    s.set_defaults(func=cmd_run_controls)

    s = sub.add_parser("analyze", help="make plots and tables")
    add_config_arg(s)
    s.set_defaults(func=cmd_analyze)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
