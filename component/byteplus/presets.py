"""BytePlus style presets loaded from centralized configuration."""

from __future__ import annotations

from config.byteplus_config import load_preset_config
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def _load() -> tuple[dict[str, Any], ...]:
    data = load_preset_config()
    if not isinstance(data, list):
        raise RuntimeError("BytePlus preset data must be a JSON array.")
    return tuple(item for item in data if isinstance(item, dict))


def list_presets() -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "name": item["name"],
            "style": dict(item["style"]),
            "category": item["category"],
            "subcategory": item["subcategory"],
            "scene_prompt": item["scene_prompt"],
        }
        for item in _load()
    ]
