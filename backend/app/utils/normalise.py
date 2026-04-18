from __future__ import annotations

import re
import string

NAME_EXPANSIONS = {
    "pvt": "private",
    "ltd": "limited",
    "co": "company",
    "mfg": "manufacturing",
    "intl": "international",
    "ind": "industries",
}
ADDRESS_EXPANSIONS = {
    "rd": "road",
    "st": "street",
    "nr": "near",
    "opp": "opposite",
    "no": "",
}
LEGAL_SUFFIXES = {"private limited", "limited", "llp"}
PINCODE_PATTERN = re.compile(r"\b(\d{6})\b")


def _strip_punctuation(value: str) -> str:
    translation = str.maketrans("", "", string.punctuation)
    return value.translate(translation)


def normalise_name(raw: str) -> str:
    value = _strip_punctuation(raw.lower())
    tokens = [NAME_EXPANSIONS.get(token, token) for token in value.split()]
    joined = " ".join(tokens)
    for suffix in LEGAL_SUFFIXES:
        joined = joined.replace(suffix, " ")
    return " ".join(joined.split())


def extract_pin_code(raw: str) -> str:
    match = PINCODE_PATTERN.search(raw)
    if not match:
        return ""
    return match.group(1)


def normalise_address(raw: str) -> str:
    lower = raw.lower().replace("no.", "").replace("#", "")
    pin_code = extract_pin_code(lower)
    cleaned = _strip_punctuation(lower)
    tokens = [ADDRESS_EXPANSIONS.get(token, token) for token in cleaned.split()]
    normalised = " ".join(token for token in tokens if token)
    normalised = " ".join(normalised.split())
    if pin_code and pin_code not in normalised:
        normalised = f"{normalised} {pin_code}".strip()
    return normalised
