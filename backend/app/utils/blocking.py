from __future__ import annotations

from typing import Any

import jellyfish

from backend.app.utils.normalise import extract_pin_code


def _get_attr(record: Any, key: str, default: str = "") -> str:
    value = getattr(record, key, default)
    return value or default


def generate_blocking_keys(record: Any) -> list[str]:
    norm_name = _get_attr(record, "norm_name")
    norm_address = _get_attr(record, "norm_address")
    pan = _get_attr(record, "pan")
    gstin = _get_attr(record, "gstin")
    first_word = norm_name.split()[0] if norm_name.split() else ""
    pin_code = extract_pin_code(norm_address) or extract_pin_code(_get_attr(record, "raw_address"))

    keys = set()
    if norm_name:
        keys.add(f"name_pin:{norm_name[:4]}:{pin_code}")
    if pan:
        keys.add(f"pan:{pan}")
    if gstin:
        keys.add(f"gst:{gstin[:10]}")
    if first_word:
        keys.add(f"soundex:{jellyfish.soundex(first_word)}")
    return sorted(key for key in keys if key)
