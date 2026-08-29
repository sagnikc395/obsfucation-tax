from __future__ import annotations


def resolve_layers(config: dict) -> list[int]:
    # priority: config["activations"]["layers"] -> config["probes"]["layers"]
    for key in ["activations", "probes", "probe"]:
        if key in config and isinstance(config[key], dict) and "layers" in config[key]:
            return list(config[key]["layers"])
    if "probes" in config and "probe" in config["probes"]:
        layers = config["probes"]["probe"].get("layers")
        if layers:
            return list(layers)
    return [12, 16, 20]


def layer_name(layer: int) -> str:
    return f"layer_{layer}"
