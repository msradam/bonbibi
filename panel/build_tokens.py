"""Resolve tokens.json (DTCG, three tiers) into CSS custom properties.

Pure function over tokens.json: walks primitive -> semantic -> component,
resolving `{a.b.c}` alias strings by path lookup. No DOM, no mode logic --
mode switching (night/sun/forced-colors) is a separate concern, since
tokens.json only fully specifies the default-mode colour palette (see
MODE_OVERRIDES below for why).

Run: python3 build_tokens.py > tokens.css
"""

import json
import os
import re

ALIAS_RE = re.compile(r"^\{([\w.-]+)\}$")

# tokens.json's semantic.mode-night only carries 5 neutral colours
# (surface/ink/rule). It has no sun or forced-colors section, and no
# mode-specific overrides for status/depth/route colours at all -- those
# exist only in the "Bonbibi Result Screen.dc.html" reference's modes()
# object. tokens.json is not yet the complete machine-readable artefact
# the design doc claims it is; this is a real gap, not a guess on our
# part. These three overrides are ported verbatim from that reference so
# the panel renders correctly today; tokens.json should gain the missing
# sun/forced-colors/full-night sections so this table can be deleted.
#
# tokens.json also never defines --depth-on-band-lo/hi or
# --depth-marker-outer/core at all (only the README prose in section 3
# mentions they're needed). DEFAULT_GAP_FILL below is the same reference's
# default-mode values for those, for the same reason.
DEFAULT_GAP_FILL = {
    "depth-on-band-lo": "#0B1A24",
    "depth-on-band-hi": "#FFFFFF",
    "depth-marker-outer": "#0B1A24",
    "depth-marker-core": "#FFFFFF",
}

MODE_OVERRIDES = {
    "night": {
        "surface-paper": "#0B0E11",
        "surface-panel": "#161B20",
        "surface-ink": "#C9D1D6",
        "surface-ink-secondary": "#8B959B",
        "surface-rule": "#2C343A",
        "status-danger": "#F0574B",
        "status-warning": "#FCBE00",
        "status-safe": "#2E8C5E",
        "status-mandatory": "#4E86B8",
        "status-no-information": "#8B959B",
        "depth-d0": "#A9BCC8",
        "depth-d1": "#7C9CB4",
        "depth-d2": "#5688B0",
        "depth-d3": "#1F4E86",
        "depth-d4": "#3A1752",
        "status-on-safe": "#FFFFFF",
        "depth-casing-low": "#0B0E11",
        "depth-casing-high": "#EDF2F5",
        "route-foot": "#2E8C5E",
        "depth-on-band-lo": "#0B0E11",
        "depth-on-band-hi": "#FFFFFF",
        "depth-marker-outer": "#05080A",
        "depth-marker-core": "#EDF2F5",
    },
    "sun": {
        "surface-paper": "#FFFFFF",
        "surface-panel": "#FFFFFF",
        "surface-ink": "#000000",
        "surface-ink-secondary": "#000000",
        "surface-rule": "#000000",
        "status-danger": "#000000",
        "status-warning": "#000000",
        "status-safe": "#000000",
        "status-mandatory": "#000000",
        "status-no-information": "#000000",
        "depth-d0": "#FFFFFF",
        "depth-d1": "#D9D9D9",
        "depth-d2": "#A6A6A6",
        "depth-d3": "#595959",
        "depth-d4": "#000000",
        "status-on-safe": "#FFFFFF",
        "depth-casing-low": "#000000",
        "depth-casing-high": "#FFFFFF",
        "route-foot": "#000000",
        "depth-on-band-lo": "#000000",
        "depth-on-band-hi": "#FFFFFF",
        "depth-marker-outer": "#000000",
        "depth-marker-core": "#FFFFFF",
    },
    "forced": {
        "surface-paper": "Canvas",
        "surface-panel": "Canvas",
        "surface-ink": "CanvasText",
        "surface-ink-secondary": "CanvasText",
        "surface-rule": "CanvasText",
        "status-danger": "CanvasText",
        "status-warning": "CanvasText",
        "status-safe": "CanvasText",
        "status-mandatory": "CanvasText",
        "status-no-information": "CanvasText",
        "depth-d0": "Canvas",
        "depth-d1": "Canvas",
        "depth-d2": "Canvas",
        "depth-d3": "Canvas",
        "depth-d4": "Canvas",
        "status-on-safe": "Canvas",
        "depth-casing-low": "CanvasText",
        "depth-casing-high": "CanvasText",
        "route-foot": "CanvasText",
        "depth-on-band-lo": "CanvasText",
        "depth-on-band-hi": "CanvasText",
        "depth-marker-outer": "CanvasText",
        "depth-marker-core": "Canvas",
    },
}


def load_tokens() -> dict:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tokens.json")
    with open(path) as f:
        return json.load(f)


def resolve(node, root):
    """Resolve one token node ($type/$value) or alias string to a CSS literal."""
    if isinstance(node, dict) and "$value" in node:
        return resolve(node["$value"], root)
    if isinstance(node, str):
        m = ALIAS_RE.match(node)
        if m:
            return resolve(lookup(m.group(1), root), root)
        return node
    if isinstance(node, dict) and "value" in node and "unit" in node:
        return f"{node['value']}{node['unit']}"
    if isinstance(node, list):
        return ", ".join(f"'{n}'" if " " in n else n for n in node)
    if isinstance(node, (int, float, bool)):
        return str(node)
    raise ValueError(f"Cannot resolve token value: {node!r}")


def lookup(path: str, root: dict):
    node = root
    for part in path.split("."):
        node = node[part]
    return node


def walk(node, prefix, root, out):
    if isinstance(node, dict) and "$value" in node:
        out[prefix] = resolve(node, root)
        return
    if isinstance(node, dict):
        for key, child in node.items():
            if key.startswith("$") or key.startswith("mode-"):
                continue  # mode-* variants are applied separately, see MODE_OVERRIDES
            walk(child, f"{prefix}-{key}" if prefix else key, root, out)


def build_css() -> str:
    tokens = load_tokens()
    flat: dict[str, str] = {}
    for tier in ("semantic", "component"):
        walk(tokens[tier], "", tokens, flat)
    flat.update(DEFAULT_GAP_FILL)

    lines = [":root {"]
    for name, value in sorted(flat.items()):
        if isinstance(value, str) and value in ("True", "False"):
            value = value.lower()
        lines.append(f"  --{name}: {value};")
    lines.append("}")

    for mode, overrides in MODE_OVERRIDES.items():
        lines.append(f'\n.frame[data-mode="{mode}"] {{')
        for name, value in overrides.items():
            lines.append(f"  --{name}: {value};")
        lines.append("}")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(build_css())
