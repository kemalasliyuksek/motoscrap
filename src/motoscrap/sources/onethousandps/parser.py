from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Any

from selectolax.parser import HTMLParser

from motoscrap.sources.base import SpecsDTO
from motoscrap.sources.onethousandps.normalize import normalize_attributes

_NUXT_DATA_SELECTOR = "script#__NUXT_DATA__"

_UNDEFINED = -1
_HOLE = -2
_NAN = -3
_POS_INFINITY = -4
_NEG_INFINITY = -5
_NEG_ZERO = -6


class NuxtPayloadError(ValueError):
    pass


def extract_nuxt_payload(html: str) -> list[Any]:
    """Return the parsed JSON array inside the `#__NUXT_DATA__` script tag."""
    tree = HTMLParser(html)
    node = tree.css_first(_NUXT_DATA_SELECTOR)
    if node is None:
        raise NuxtPayloadError("No __NUXT_DATA__ script tag found")
    raw = node.text(deep=True).strip()
    if not raw:
        raise NuxtPayloadError("Empty __NUXT_DATA__ script tag")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NuxtPayloadError(f"Invalid JSON in __NUXT_DATA__: {exc}") from exc
    if not isinstance(parsed, list):
        raise NuxtPayloadError("__NUXT_DATA__ root is not an array")
    return parsed


def unflatten(payload: list[Any]) -> Any:
    """Resolve devalue-flattened payload into a plain Python object graph.

    See https://github.com/Rich-Harris/devalue for the format spec.
    """
    cache: dict[int, Any] = {}

    def resolve(index: int) -> Any:
        if index == _UNDEFINED:
            return None
        if index == _HOLE:
            return None
        if index == _NAN:
            return float("nan")
        if index == _POS_INFINITY:
            return float("inf")
        if index == _NEG_INFINITY:
            return float("-inf")
        if index == _NEG_ZERO:
            return -0.0
        if index in cache:
            return cache[index]
        raw = payload[index]
        if isinstance(raw, (str, int, float, bool)) or raw is None:
            cache[index] = raw
            return raw
        if isinstance(raw, list):
            resolved_list: list[Any] = []
            cache[index] = resolved_list
            for item in raw:
                if isinstance(item, int):
                    resolved_list.append(resolve(item))
                else:
                    resolved_list.append(item)
            return resolved_list
        if isinstance(raw, dict):
            if len(raw) == 1 and next(iter(raw)) in {
                "Date",
                "Set",
                "Map",
                "BigInt",
                "null",
                "RegExp",
                "Error",
            }:
                type_tag = next(iter(raw))
                value = raw[type_tag]
                if type_tag == "Date":
                    resolved = payload[value] if isinstance(value, int) else value
                    cache[index] = resolved
                    return resolved
                if type_tag == "Set":
                    resolved_set = [resolve(i) for i in value]
                    cache[index] = resolved_set
                    return resolved_set
                if type_tag == "Map":
                    result_map: dict[Any, Any] = {}
                    cache[index] = result_map
                    for i in range(0, len(value), 2):
                        k = resolve(value[i])
                        v = resolve(value[i + 1])
                        result_map[k] = v
                    return result_map
                cache[index] = value
                return value
            resolved_dict: dict[str, Any] = {}
            cache[index] = resolved_dict
            for key, ref in raw.items():
                if isinstance(ref, int):
                    resolved_dict[key] = resolve(ref)
                else:
                    resolved_dict[key] = ref
            return resolved_dict
        cache[index] = raw
        return raw

    if not payload:
        return None
    return resolve(0)


def _walk(obj: Any) -> Iterator[Any]:
    stack = [obj]
    seen: set[int] = set()
    while stack:
        current = stack.pop()
        ident = id(current)
        if ident in seen:
            continue
        seen.add(ident)
        yield current
        if isinstance(current, dict):
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)


def _find_bike_root(tree: Any) -> dict[str, Any] | None:
    """Find the first dict carrying motorcycle catalog keys (modelId+technicalData)."""
    for node in _walk(tree):
        if (
            isinstance(node, dict)
            and "modelId" in node
            and "technicalData" in node
            and "brandName" in node
        ):
            return node
    return None


_YEAR_FROM_TITLE = re.compile(r"\b(19|20)\d{2}\b")

# Preferred locales used only to pick a stable key for attribute/group names
# (those drive the normaliser). Values themselves are stored with every locale
# the source exposes, so downstream consumers can pick their own.
_KEY_LOCALE_PREFERENCES = ("tr-tr", "tr", "en-gb", "en")

I18N_MARKER = "_i18n"


def _all_translations(value: Any) -> dict[str, str] | None:
    """Return every locale string from a 1000ps translation object."""
    if isinstance(value, dict) and isinstance(value.get("translations"), dict):
        translations = {
            str(k): v for k, v in value["translations"].items() if isinstance(v, str) and v != ""
        }
        return translations or None
    return None


def _pick_key_locale(translations: dict[str, str]) -> str | None:
    for locale in _KEY_LOCALE_PREFERENCES:
        hit = translations.get(locale)
        if hit:
            return hit
    return next(iter(translations.values()), None)


def _translation_key(value: Any) -> str | None:
    if isinstance(value, dict):
        key = value.get("translationKey")
        if isinstance(key, str) and key:
            return key
    return None


def _translate_scalar(value: Any) -> str | None:
    """Collapse a translation object to a single preferred-locale string."""
    translations = _all_translations(value)
    if translations is not None:
        return _pick_key_locale(translations)
    if isinstance(value, (str, int, float)) and value != "":
        return str(value)
    return None


def _extract_value(value_num: Any, value_select: Any) -> Any:
    """Derive a final attribute value.

    Numbers come back as-is. Categorical values come back as:
      * a plain string when the source offers no translations for it, or
      * `{"_i18n": {locale: text, ...}}` when translations are available.

    When multiple translated items are present (multi-select), each locale
    has them joined with a comma.
    """
    if value_num is not None:
        return value_num
    if not isinstance(value_select, list) or not value_select:
        return None

    locales: set[str] = set()
    per_item_translations: list[dict[str, str] | None] = []
    per_item_fallback: list[str | None] = []
    for item in value_select:
        translations = _all_translations(item)
        per_item_translations.append(translations)
        if translations is not None:
            locales.update(translations.keys())
            per_item_fallback.append(None)
        elif isinstance(item, (str, int, float)) and str(item) != "":
            per_item_fallback.append(str(item))
        else:
            per_item_fallback.append(None)

    if locales:
        merged: dict[str, str] = {}
        for locale in locales:
            parts: list[str] = []
            for translations, fallback in zip(
                per_item_translations, per_item_fallback, strict=True
            ):
                if translations is not None:
                    picked = translations.get(locale)
                    if picked:
                        parts.append(picked)
                elif fallback is not None:
                    parts.append(fallback)
            if parts:
                merged[locale] = ", ".join(parts)
        if not merged:
            return None
        return {I18N_MARKER: merged}

    strings = [s for s in per_item_fallback if s]
    if not strings:
        return None
    return ", ".join(strings)


def parse_specs(html: str, *, fallback_year: int | None = None) -> SpecsDTO:
    """Parse a 1000ps.com model page into a SpecsDTO.

    `fallback_year` is used when the page does not expose an explicit year
    (the "all years" URL). If the payload has `modelYear`, that wins.
    """
    payload = extract_nuxt_payload(html)
    tree = unflatten(payload)
    root = _find_bike_root(tree)
    if root is None:
        raise NuxtPayloadError("No motorcycle root node in payload")

    raw_entries: list[dict[str, Any]] = []
    technical = root.get("technicalData") or {}
    groups = technical.get("groups") or []
    for group in groups:
        group_name_key = _translate_scalar(group.get("groupName"))
        group_translation_key = _translation_key(group.get("groupName"))
        entries = group.get("entries") or []
        for entry in entries:
            attr_name_key = _translate_scalar(entry.get("attributeName"))
            attr_translation_key = _translation_key(entry.get("attributeName"))
            unit = _translate_scalar(entry.get("attributeUnit"))
            value = _extract_value(entry.get("valueNumber"), entry.get("valueSelect"))
            if attr_translation_key is None or value is None or value == "":
                continue
            raw_entries.append(
                {
                    "group": group_name_key or "",
                    "group_key": group_translation_key,
                    "attribute": attr_name_key or attr_translation_key,
                    "attribute_key": attr_translation_key,
                    "value": value,
                    "unit": unit,
                }
            )

    grouped = normalize_attributes(raw_entries)

    year = root.get("modelYear")
    if year is None:
        tree_html = HTMLParser(html)
        title_node = tree_html.css_first("title")
        title = title_node.text() if title_node else ""
        match = _YEAR_FROM_TITLE.search(title)
        year = int(match.group(0)) if match else fallback_year
    if year is None:
        raise NuxtPayloadError("Could not determine model year")

    brand = root.get("brandName") or ""
    model_name = root.get("modelName") or ""
    display_name = f"{brand} {model_name} - {year}".strip().upper()

    return SpecsDTO(
        year=int(year),
        display_name=display_name,
        grouped=grouped,
        raw={str(e["attribute_key"]): e["value"] for e in raw_entries},
    )


def _summarise_value_for_raw(value: Any) -> Any:
    if isinstance(value, dict) and I18N_MARKER in value:
        return value[I18N_MARKER]
    return value


def merge_specs(primary: SpecsDTO, secondaries: list[SpecsDTO]) -> SpecsDTO:
    """Merge translations from `secondaries` into `primary`.

    Numeric values and structure come from `primary`. For categorical values
    (those wrapped in `_i18n`), locale translations from secondaries are added
    alongside the primary's translations.
    """
    merged_grouped: dict[str, dict[str, Any]] = {}
    for group_key, group_value in primary.grouped.items():
        merged_group = {k: _deep_copy_value(v) for k, v in group_value.items()}
        merged_grouped[group_key] = merged_group

    for other in secondaries:
        for group_key, group_value in other.grouped.items():
            target_group = merged_grouped.setdefault(group_key, {})
            for attr_key, other_value in group_value.items():
                if attr_key not in target_group:
                    target_group[attr_key] = _deep_copy_value(other_value)
                    continue
                target_value = target_group[attr_key]
                target_group[attr_key] = _merge_value(target_value, other_value)

    merged_raw = {**primary.raw}
    for other in secondaries:
        for key, value in other.raw.items():
            merged_raw.setdefault(key, value)

    return SpecsDTO(
        year=primary.year,
        display_name=primary.display_name,
        grouped=merged_grouped,
        raw=merged_raw,
    )


def _deep_copy_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _deep_copy_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_copy_value(v) for v in value]
    return value


def _merge_value(target: Any, other: Any) -> Any:
    target_is_i18n = isinstance(target, dict) and I18N_MARKER in target
    other_is_i18n = isinstance(other, dict) and I18N_MARKER in other

    if target_is_i18n and other_is_i18n:
        merged = dict(target[I18N_MARKER])
        for locale, text in other[I18N_MARKER].items():
            merged.setdefault(locale, text)
        return {I18N_MARKER: merged}
    if target_is_i18n:
        return target
    if other_is_i18n:
        return other
    return target


def parse_existing_model_years(html: str) -> list[int]:
    payload = extract_nuxt_payload(html)
    tree = unflatten(payload)
    root = _find_bike_root(tree)
    if root is None:
        return []
    years = root.get("existingModelYears") or []
    return sorted({int(y) for y in years if isinstance(y, (int, str)) and str(y).isdigit()})


def parse_model_metadata(html: str) -> dict[str, Any]:
    """Extract top-level model metadata (brand, model name, ids)."""
    payload = extract_nuxt_payload(html)
    tree = unflatten(payload)
    root = _find_bike_root(tree)
    if root is None:
        raise NuxtPayloadError("No motorcycle root node in payload")
    return {
        "model_id": root.get("modelId"),
        "model_name": root.get("modelName"),
        "brand_id": root.get("brandId"),
        "brand_name": root.get("brandName"),
        "existing_model_years": parse_existing_model_years(html),
    }
