from __future__ import annotations

from pathlib import Path
import csv


def write_csv(rows: list[dict], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("")
        return p
    # union of all keys to handle heterogeneous rows
    fieldnames = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)
    with open(p, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return p


def write_markdown_table(rows: list[dict], path: str | Path, title: str | None = None) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("")
        return p
    # union of keys
    cols = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                cols.append(k)
    lines = []
    if title:
        lines.append(f"# {title}\n")
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    p.write_text("\n".join(lines) + "\n")
    return p


def confound_controls_markdown(rows: list[dict], path: str | Path) -> Path:
    return write_markdown_table(rows, path, title="Confound Controls")


def main_results_markdown(rows: list[dict], path: str | Path) -> Path:
    return write_markdown_table(rows, path, title="Main Results")
