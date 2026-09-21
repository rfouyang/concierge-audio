"""Normalized BytePlus TTS 2.0 catalog captured from the official voice list."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def _load() -> tuple[dict[str, Any], ...]:
    path = Path(__file__).with_name("voices_data.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("BytePlus voice data must be a JSON array.")
    return tuple(item for item in data if isinstance(item, dict))


def list_voices() -> list[dict[str, Any]]:
    return [dict(item) for item in _load()]
