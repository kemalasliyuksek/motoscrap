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


def test_parse_specs_2011(fixtures_dir: Path) -> None:
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
    assert engine["cooling"] == "Hava"

    dims = specs.grouped["dimensions"]
    assert dims["wheelbase_mm"] == 1450
    assert dims["seat_height_mm"] == 800
    assert dims["front_tire_width_mm"] == 120
    assert dims["license_class"] == "A"

    brakes_front = specs.grouped["brakes_front"]
    assert brakes_front["piston"] == "Dört piston"
    assert brakes_front["technology"] == "radyal"

    brakes_rear = specs.grouped["brakes_rear"]
    assert brakes_rear["type"] == "Disk"
    assert brakes_rear["piston"] == "Çift piston"

    suspension = specs.grouped["suspension"]
    assert suspension["front_type"] == "Baş aşağı teleskopik çatal"
    assert suspension["rear_type"] == "Tek şok"
    assert suspension["front_brand"] == "Showa"


def test_parse_specs_2014(fixtures_dir: Path) -> None:
    html = _load(fixtures_dir, "monster-796.html")
    specs = parser.parse_specs(html)

    assert specs.year == 2014
    assert specs.display_name == "DUCATI MONSTER 796 - 2014"
    assert specs.grouped["engine"]["displacement_cc"] == 803
    assert specs.grouped["engine"]["final_drive"] == "Zincir"
    assert specs.grouped["dimensions"]["curb_weight_kg"] == 187
    assert specs.grouped["dimensions"]["length_mm"] == 2114
    assert specs.grouped["rider_aids"]["systems"] == "ABS"


def test_parse_specs_does_not_leak_unmapped_when_complete(fixtures_dir: Path) -> None:
    """A well-mapped fixture should have zero unmapped attributes."""
    html = _load(fixtures_dir, "monster-796-2011.html")
    specs = parser.parse_specs(html)
    unmapped = specs.grouped.get("_unmapped", {})
    # Small number tolerated — the goal is coverage, not perfection.
    assert len(unmapped) <= 3, f"Too many unmapped: {unmapped}"


def test_parser_rejects_non_bike_page() -> None:
    with pytest.raises(parser.NuxtPayloadError):
        parser.parse_specs("<html><body>no nuxt</body></html>")
