from __future__ import annotations

# Control prompts: same sandbagging prompt but honest generation, etc.

CONTROL_CONDITIONS = {
    "prompt_leakage_control": {
        "description": "Sandbagging prompt but model instructed to answer honestly (isolates prompt leakage)",
        "template_id": "prompt_leakage_control",
    },
    "heldout_template": {
        "description": "Held-out phrasing to test template overfit",
        "template_id": "heldout_template",
    },
}
