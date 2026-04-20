from __future__ import annotations

from typing import Any

I18N_MARKER = "_i18n"

DEFAULT_FALLBACK_LOCALES: tuple[str, ...] = ("en-gb", "en", "tr-tr", "tr")


def flatten_specs(specs: dict[str, Any], locale: str | None) -> dict[str, Any]:
    """Collapse translation wrappers to flat strings in the requested locale.

    When `locale` is None, the structure is returned unchanged so callers can
    inspect or serve all available translations.
    """
    if locale is None:
        return specs
    chain = _fallback_chain(locale)
    flat = _flatten(specs, chain)
    assert isinstance(flat, dict)
    return flat


def available_locales(specs: dict[str, Any]) -> list[str]:
    """Return the union of locale codes present in any translated value."""
    seen: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if I18N_MARKER in value and isinstance(value[I18N_MARKER], dict):
                seen.update(value[I18N_MARKER].keys())
            else:
                for v in value.values():
                    visit(v)
        elif isinstance(value, list):
            for v in value:
                visit(v)

    visit(specs)
    return sorted(seen)


def _fallback_chain(locale: str) -> list[str]:
    key = locale.lower().strip()
    chain: list[str] = [key]
    if "-" in key:
        chain.append(key.split("-", 1)[0])
    for default in DEFAULT_FALLBACK_LOCALES:
        if default not in chain:
            chain.append(default)
    return chain


def _flatten(value: Any, chain: list[str]) -> Any:
    if isinstance(value, dict):
        if I18N_MARKER in value and isinstance(value[I18N_MARKER], dict):
            return _pick(value[I18N_MARKER], chain)
        return {str(k): _flatten(v, chain) for k, v in value.items()}
    if isinstance(value, list):
        return [_flatten(v, chain) for v in value]
    return value


def _pick(translations: dict[str, str], chain: list[str]) -> str | None:
    lowered = {k.lower(): v for k, v in translations.items()}
    for candidate in chain:
        text = lowered.get(candidate)
        if text:
            return text
        # Broaden: if user asked for a bare language like "tr", accept any
        # "tr-*" that is present (e.g. "tr-tr").
        if "-" not in candidate:
            for code, text in lowered.items():
                if code.startswith(f"{candidate}-") and text:
                    return text
    for text in translations.values():
        if text:
            return text
    return None
