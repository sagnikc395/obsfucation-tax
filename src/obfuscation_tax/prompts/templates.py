from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import load_yaml


def load_templates(config: dict[str, Any] | None = None, path: str | Path = "configs/prompts.yaml") -> dict[str, dict[str, str]]:
    if config is not None and "prompts" in config:
        # config loaded via load_config nests prompts.yaml under "prompts"
        p = config["prompts"]
        # It contains "templates" key
        if "templates" in p:
            return p["templates"]
        return p
    if Path(path).exists():
        data = load_yaml(path)
        return data.get("templates", {})
    return {}


def render_template(template: str, question: str) -> str:
    return template.format(question=question)


def get_template(template_id: str, config: dict[str, Any] | None = None) -> dict[str, str]:
    templates = load_templates(config)
    if template_id not in templates:
        raise KeyError(f"template {template_id} not found. Available: {list(templates.keys())}")
    return templates[template_id]


def render_prompt(template_id: str, question: str, config: dict[str, Any] | None = None) -> tuple[str, str]:
    """Return (prompt_text, condition)."""
    tmpl = get_template(template_id, config)
    text = render_template(tmpl["template"], question)
    condition = tmpl.get("condition", "unknown")
    return text, condition
