from __future__ import annotations

CONDITIONS = ["honest", "sandbag_r0", "sandbag_r1", "prompt_leakage_control", "heldout_template"]

# Default mapping from condition -> template id (overridable via config)
DEFAULT_CONDITION_TEMPLATES = {
    "honest": "honest_v1",
    "sandbag_r0": "sandbag_r0_v1",
    "sandbag_r1": "sandbag_r1_v1",
    "prompt_leakage_control": "prompt_leakage_control",
    "heldout_template": "heldout_template",
}


def template_for_condition(condition: str, config: dict | None = None) -> str:
    if config and "prompts" in config:
        defaults = config["prompts"].get("defaults", {})
        if condition in defaults:
            return defaults[condition]
    return DEFAULT_CONDITION_TEMPLATES.get(condition, "honest_v1")


def is_sandbagging_condition(condition: str) -> bool:
    return condition in ("sandbag_r0", "sandbag_r1", "heldout_template")
