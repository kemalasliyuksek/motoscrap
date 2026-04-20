from pathlib import Path

import pytest

from motoscrap.sources.onethousandps import parser


def _load(fixtures_dir: Path, name: str) -> str:
    return (fixtures_dir / "onethousandps" / name).read_text(encoding="utf-8")


def test_parse_model_metadata(fixtures_dir: Path) -> None:
    html = _load(fixtures_dir, "monster-796-2011.html")
    meta = parser.parse_model_metadata(html)
    assert meta["model_id"] == 4952
    assert meta["model_name"] == "Monster 796"
    assert meta["brand_id"] == 5
    assert meta["brand_name"] == "Ducati"
    assert set(meta["existing_model_years"]) == {2010, 2011, 2012, 2013, 2014}


def test_parse_existing_model_years(fixtures_dir: Path) -> None:
    html = _load(fixtures_dir, "monster-796.html")
    years = parser.parse_existing_model_years(html)
    assert 2011 in years
    assert 2014 in years


def test_parse_specs_2011_tr(fixtures_dir: Path) -> None:
    html = _load(fixtures_dir, "monster-796-2011.html")
    specs = parser.parse_specs(html)

    assert specs.year == 2011
    assert specs.display_name == "DUCATI MONSTER 796 - 2011"

    engine = specs.grouped["engine"]
    assert engine["bore_mm"] == 88
    assert engine["stroke_mm"] == 66
    assert engine["power_hp"] == 87
    assert engine["torque_nm"] == 78
    assert engine["displacement_cc"] == 803

    cooling = engine["cooling"]
    assert isinstance(cooling, dict) and "_i18n" in cooling
    assert cooling["_i18n"].get("tr-tr") == "Hava"

    dims = specs.grouped["dimensions"]
    assert dims["wheelbase_mm"] == 1450
    assert dims["seat_height_mm"] == 800
    assert dims["license_class"]["_i18n"]["tr-tr"] == "A"


def test_parse_specs_2014_carries_multiple_locales(fixtures_dir: Path) -> None:
    html = _load(fixtures_dir, "monster-796.html")
    specs = parser.parse_specs(html)

    assert specs.year == 2014
    assert specs.display_name == "DUCATI MONSTER 796 - 2014"
    assert specs.grouped["engine"]["displacement_cc"] == 803
    assert specs.grouped["dimensions"]["curb_weight_kg"] == 187

    cooling = specs.grouped["engine"]["cooling"]
    assert cooling["_i18n"]["tr"] == "Hava"
    assert cooling["_i18n"]["en"] == "Air"
    assert cooling["_i18n"]["de"] == "Luft"

    rider_aids = specs.grouped["rider_aids"]["systems"]
    assert rider_aids["_i18n"]["tr"] == "ABS"


def test_merge_specs_unions_locales(fixtures_dir: Path) -> None:
    tr = parser.parse_specs(_load(fixtures_dir, "monster-796-2011.html"))
    en = parser.parse_specs(_load(fixtures_dir, "monster-796-2011-en.html"))
    merged = parser.merge_specs(tr, [en])

    assert merged.year == 2011
    cooling = merged.grouped["engine"]["cooling"]
    assert cooling["_i18n"].get("tr-tr") == "Hava"
    assert cooling["_i18n"].get("en-gb") == "Air"

    # Numeric values survive unchanged
    assert merged.grouped["engine"]["bore_mm"] == 88
    assert merged.grouped["dimensions"]["wheelbase_mm"] == 1450


def test_parser_rejects_non_bike_page() -> None:
    with pytest.raises(parser.NuxtPayloadError):
        parser.parse_specs("<html><body>no nuxt</body></html>")
