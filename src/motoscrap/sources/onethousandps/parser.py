from __future__ import annotations

import json
import re
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


def _walk(obj: Any):
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

_LOCALE_PREFERENCES = ("tr-tr", "tr", "en-gb", "en")


def _translate(value: Any) -> Any:
    """Pick the locale string out of a translation object, or passthrough."""
    if isinstance(value, dict) and "translations" in value:
        translations = value.get("translations") or {}
        if not isinstance(translations, dict):
            return None
        for locale in _LOCALE_PREFERENCES:
            hit = translations.get(locale)
            if hit is not None and hit != "":
                return hit
        return None
    return value


def _translate_select(value: Any) -> Any:
    """A valueSelect is a list of translation objects or strings; return a joined str or None."""
    if value is None:
        return None
    if isinstance(value, list):
        items = [_translate(item) for item in value]
        items = [str(i) for i in items if i is not None and i != ""]
        if not items:
            return None
        if len(items) == 1:
            return items[0]
        return ", ".join(items)
    return _translate(value)


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
        group_name = _translate(group.get("groupName"))
        entries = group.get("entries") or []
        for entry in entries:
            attr_name = _translate(entry.get("attributeName"))
            unit = _translate(entry.get("attributeUnit"))
            value_num = entry.get("valueNumber")
            value_select = _translate_select(entry.get("valueSelect"))
            value = value_num if value_num is not None else value_select
            if attr_name is None or value is None or value == "":
                continue
            raw_entries.append(
                {
                    "group": group_name,
                    "attribute": str(attr_name),
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
        raw={f"{e['group']}::{e['attribute']}": e["value"] for e in raw_entries},
    )


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
