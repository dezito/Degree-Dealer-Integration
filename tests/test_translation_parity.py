"""Translation parity across languages.

Covers the dashboard texts (texts/*.json) and the Home Assistant translations
(strings.json and translations/*.json): same keys in every language, same
{placeholder} names per key, and a minimum key count so an empty or truncated
file cannot pass.

Partial parity checks that already exist and are left alone:
test_dashboard.py::test_every_language_has_the_same_texts_and_all_used_keys
(texts key set and template usage only).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

INTEGRATION = Path(__file__).resolve().parents[1] / "custom_components" / "degree_dealer"
TEXTS_DIR = INTEGRATION / "texts"
TRANSLATIONS_DIR = INTEGRATION / "translations"
STRINGS_FILE = INTEGRATION / "strings.json"

LANGUAGES = {"da", "de", "en", "pl", "uk"}
MIN_TEXT_KEYS = 70  # texts/*.json holds 79 keys today
MIN_TRANSLATION_KEYS = 150  # strings.json and translations/*.json hold 176 today

PLACEHOLDER = re.compile(r"\{([a-zA-Z_0-9]+)\}")
REFERENCE = re.compile(r"^\[%key:[^%]+%\]$")


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    """Map nested dicts and lists to dotted keys; list items use their index."""
    if isinstance(value, dict):
        items = ((f"{prefix}.{key}" if prefix else str(key), item) for key, item in value.items())
    elif isinstance(value, list):
        items = ((f"{prefix}.{index}", item) for index, item in enumerate(value))
    else:
        return {prefix: value}
    flat: dict[str, Any] = {}
    for key, item in items:
        flat.update(_flatten(item, key))
    return flat


def _load(path: Path) -> dict[str, Any]:
    return _flatten(json.loads(path.read_text(encoding="utf-8")))


def _placeholders(value: Any) -> set[str]:
    if not isinstance(value, str):
        return set()
    return set(PLACEHOLDER.findall(value))


def _language_stems(directory: Path) -> set[str]:
    return {path.stem for path in directory.glob("*.json")}


def test_flatten_uses_dots_and_list_indexes() -> None:
    nested = {"a": {"b": [{"c": "x"}, "y"]}, "d": "z"}
    assert _flatten(nested) == {"a.b.0.c": "x", "a.b.1": "y", "d": "z"}


def test_placeholders_are_found() -> None:
    assert _placeholders("{room}: {temperature} °C") == {"room", "temperature"}
    assert _placeholders("no placeholder") == set()


def test_language_files_are_exactly_the_supported_set() -> None:
    assert _language_stems(TEXTS_DIR) == LANGUAGES
    assert _language_stems(TRANSLATIONS_DIR) == LANGUAGES


def test_texts_have_enough_keys() -> None:
    for language in LANGUAGES:
        assert len(_load(TEXTS_DIR / f"{language}.json")) >= MIN_TEXT_KEYS, language


def test_translations_have_enough_keys() -> None:
    assert len(_load(STRINGS_FILE)) >= MIN_TRANSLATION_KEYS
    for language in LANGUAGES:
        assert len(_load(TRANSLATIONS_DIR / f"{language}.json")) >= MIN_TRANSLATION_KEYS, language


def test_texts_have_the_same_keys_in_every_language() -> None:
    english = set(_load(TEXTS_DIR / "en.json"))
    for language in LANGUAGES:
        keys = set(_load(TEXTS_DIR / f"{language}.json"))
        assert keys == english, (language, sorted(keys ^ english))


def test_texts_keep_the_same_placeholders() -> None:
    english = _load(TEXTS_DIR / "en.json")
    for language in LANGUAGES:
        values = _load(TEXTS_DIR / f"{language}.json")
        for key, value in english.items():
            assert _placeholders(values[key]) == _placeholders(value), (language, key)


def test_translations_have_the_same_keys_as_strings() -> None:
    strings = set(_load(STRINGS_FILE))
    for language in LANGUAGES:
        keys = set(_load(TRANSLATIONS_DIR / f"{language}.json"))
        assert keys == strings, (language, sorted(keys ^ strings))


def test_translations_keep_the_same_placeholders() -> None:
    strings = _load(STRINGS_FILE)
    english = _load(TRANSLATIONS_DIR / "en.json")
    for language in LANGUAGES:
        values = _load(TRANSLATIONS_DIR / f"{language}.json")
        for key, source in strings.items():
            # A [%key:...%] reference points at another entry, so its text is not
            # checked here; the entry it points to is checked under its own key.
            if isinstance(source, str) and REFERENCE.match(source):
                continue
            assert _placeholders(values[key]) == _placeholders(english[key]), (language, key)
