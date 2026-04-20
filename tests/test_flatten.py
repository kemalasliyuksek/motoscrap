from motoscrap.services.flatten import available_locales, flatten_specs


def test_flatten_keeps_numeric_values_intact() -> None:
    specs = {
        "engine": {
            "bore_mm": 88,
            "cooling": {"_i18n": {"tr-tr": "Hava", "en": "Air"}},
        }
    }
    result = flatten_specs(specs, "en")
    assert result["engine"]["bore_mm"] == 88
    assert result["engine"]["cooling"] == "Air"


def test_flatten_without_locale_returns_raw() -> None:
    specs = {"engine": {"cooling": {"_i18n": {"tr-tr": "Hava", "en": "Air"}}}}
    assert flatten_specs(specs, None) is specs


def test_flatten_falls_back_through_bcp47_chain() -> None:
    specs = {"engine": {"cooling": {"_i18n": {"de": "Luft", "en": "Air"}}}}
    # "de-de" not present, falls back to "de"
    assert flatten_specs(specs, "de-de")["engine"]["cooling"] == "Luft"


def test_flatten_falls_back_to_en_then_tr() -> None:
    specs = {"engine": {"cooling": {"_i18n": {"tr-tr": "Hava"}}}}
    # "fr" not in translations → fr → en → en-gb → tr-tr
    assert flatten_specs(specs, "fr")["engine"]["cooling"] == "Hava"


def test_flatten_broadens_bare_language_to_regional_variant() -> None:
    """Asking for 'tr' finds 'tr-tr' even though the short code is not listed."""
    specs = {"engine": {"cooling": {"_i18n": {"tr-tr": "Hava", "en-gb": "Air"}}}}
    assert flatten_specs(specs, "tr")["engine"]["cooling"] == "Hava"
    assert flatten_specs(specs, "en")["engine"]["cooling"] == "Air"


def test_flatten_uses_any_locale_as_last_resort() -> None:
    specs = {"engine": {"cooling": {"_i18n": {"xx": "Something"}}}}
    assert flatten_specs(specs, "fr")["engine"]["cooling"] == "Something"


def test_available_locales_unions_all_translations() -> None:
    specs = {
        "engine": {
            "cooling": {"_i18n": {"tr-tr": "Hava", "en": "Air"}},
            "valve_train": {"_i18n": {"en": "Desmodromic", "de": "Desmodromik"}},
        },
        "dimensions": {"wheelbase_mm": 1450},
    }
    assert available_locales(specs) == ["de", "en", "tr-tr"]
