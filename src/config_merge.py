"""合并基础 config.yaml 与 Web 可写覆盖项"""

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import yaml


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def write_merged_config(
    base_path: Path, override_path: Path, output_path: Path
) -> None:
    base = {}
    if base_path.exists():
        with open(base_path, "r", encoding="utf-8") as f:
            base = yaml.safe_load(f) or {}

    override = {}
    if override_path.exists():
        with open(override_path, "r", encoding="utf-8") as f:
            override = yaml.safe_load(f) or {}

    merged = deep_merge(base, override)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            merged,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
