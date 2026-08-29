from __future__ import annotations

from pathlib import Path
from typing import Any
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def compute_tax_curve(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rows must have evasion_strength, probe_auroc, attack_strength (accuracy_drop), suspicion."""
    return sorted(rows, key=lambda r: r.get("evasion_strength", 0))


def plot_tax_curve(rows: list[dict[str, Any]], out_path: str | Path) -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = compute_tax_curve(rows)
    x = [r["evasion_strength"] for r in rows]
    y_probe = [r["probe_auroc"] for r in rows]
    y_attack = [r.get("attack_strength", 0) for r in rows]
    y_susp = [r.get("suspicion", 0) for r in rows]

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(x, y_probe, marker="o", label="Probe AUROC", color="tab:blue")
    ax1.set_xlabel("Evasion strength")
    ax1.set_ylabel("Probe AUROC", color="tab:blue")
    ax1.set_ylim(0.4, 1.0)

    ax2 = ax1.twinx()
    ax2.plot(x, y_attack, marker="s", label="Accuracy drop", color="tab:red")
    ax2.plot(x, y_susp, marker="^", label="Suspicion", color="tab:green")
    ax2.set_ylabel("Attack strength / Suspicion", color="tab:red")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")
    plt.title("Obfuscation Tax Curve")
    plt.tight_layout()
    plt.savefig(p, dpi=150)
    plt.close()
    return p


def save_tax_csv(rows: list[dict[str, Any]], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return p
    with open(p, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return p
