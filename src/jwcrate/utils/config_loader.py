import yaml
from pathlib import Path
from typing import Any, Dict

def load_yaml(filepath: Path, defaults: Dict[str, Any] = None) -> Dict[str, Any]:
    if not filepath.exists():
        if defaults is not None:
            save_yaml(filepath, defaults)
        return defaults or {}
    try:
        with filepath.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return defaults or {}
        if defaults:
            return _deep_merge(defaults, data)
        return data
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return defaults or {}

def save_yaml(filepath: Path, data: Dict[str, Any]) -> None:
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except Exception as e:
        print(f"Error saving {filepath}: {e}")

def _deep_merge(defaults: dict, overrides: dict) -> dict:
    result = dict(defaults)
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
