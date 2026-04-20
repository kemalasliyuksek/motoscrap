from __future__ import annotations

from typing import Any

# Stable English keys grouped by section. The left-hand side is the Turkish
# attribute name as exposed by 1000ps's /tr-tr/ locale. Diacritics matter.
_ATTR_MAP: dict[str, tuple[str, str]] = {
    # Engine & transmission
    "Çap": ("engine", "bore_mm"),
    "Strok": ("engine", "stroke_mm"),
    "Motor gücü": ("engine", "power_hp"),
    "Maks. Güçte dev/dak": ("engine", "power_rpm"),
    "Tork": ("engine", "torque_nm"),
    "Torkta dev/dak": ("engine", "torque_rpm"),
    "Sıkıştırma Oranı": ("engine", "compression_ratio"),
    "Şanzıman": ("engine", "final_drive"),
    "Silindirler": ("engine", "cylinders"),
    "Silindir başına supap": ("engine", "valves_per_cylinder"),
    "Subaplar": ("engine", "valve_train"),
    "Soğutma": ("engine", "cooling"),
    "Hacim": ("engine", "displacement_cc"),
    "Yakıt sistemi": ("engine", "fuel_system"),
    "Silindir başına enjektör": ("engine", "injectors_per_cylinder"),
    "Kavrama Tipi": ("engine", "clutch_type"),
    "Şanzıman Tipi": ("engine", "gearbox_type"),
    "Dişli sayısı": ("engine", "gear_count"),
    # Suspension attributes tied to the front group
    "Ön süspansiyon": ("suspension", "front_type"),
    "Darbe emici": ("suspension", "rear_type"),
    # Chassis
    "Kasa": ("chassis", "frame_material"),
    "Kasa türü": ("chassis", "frame_type"),
    # ADAS / rider aids
    "Gelişmiş Sürücü Destek Sistemleri": ("rider_aids", "systems"),
    # Dimensions & weights
    "Ön lastik genişliği": ("dimensions", "front_tire_width_mm"),
    "Ön lastik yüksekliği": ("dimensions", "front_tire_aspect_ratio"),
    "Ön lastik çapı": ("dimensions", "front_tire_rim_inch"),
    "Arka lastik genişliği": ("dimensions", "rear_tire_width_mm"),
    "Arka lastik yüksekliği": ("dimensions", "rear_tire_aspect_ratio"),
    "Arka lastik çapı": ("dimensions", "rear_tire_rim_inch"),
    "Boy": ("dimensions", "length_mm"),
    "Yükseklik": ("dimensions", "height_mm"),
    "Aks mesafesi": ("dimensions", "wheelbase_mm"),
    "Koltuk yüksekliği": ("dimensions", "seat_height_mm"),
    "Kuru Ağırlık": ("dimensions", "dry_weight_kg"),
    "Boş Ağırlık": ("dimensions", "curb_weight_kg"),
    "Yakıt Deposu Kapasitesi": ("dimensions", "fuel_tank_l"),
    "Lisansa uygunluk": ("dimensions", "license_class"),
}

# Attribute names that appear under multiple groups and must be routed by
# their source group. The value is a lookup from substring -> (group, key).
# The substring is matched against the lowercased source group name.
_CONTEXTUAL_ATTRS: dict[str, list[tuple[str, str, str]]] = {
    "Marka": [
        ("ön", "suspension", "front_brand"),
        ("arka", "suspension", "rear_brand"),
        ("fren", "brakes", "brand"),
    ],
    "Piston": [
        ("arka", "brakes_rear", "piston"),
        ("ön", "brakes_front", "piston"),
        ("fren", "brakes_front", "piston"),
    ],
    "Tipi": [
        ("arka", "brakes_rear", "type"),
        ("ön", "brakes_front", "type"),
        ("fren", "brakes_front", "type"),
    ],
    "Teknoloji": [
        ("arka", "brakes_rear", "technology"),
        ("ön", "brakes_front", "technology"),
        ("fren", "brakes_front", "technology"),
    ],
    "Çap": [
        # Chassis "Çap" is engine bore (handled by _ATTR_MAP). In suspension
        # or brake groups it means a tube/disc diameter.
        ("süspansiyon", "suspension", "fork_tube_diameter_mm"),
        ("fren", "brakes_front", "disc_diameter_mm"),
    ],
}


def _route_contextual(attribute: str, group: str) -> tuple[str, str] | None:
    rules = _CONTEXTUAL_ATTRS.get(attribute)
    if rules is None:
        return None
    group_lower = group.lower()
    for needle, target_group, target_key in rules:
        if needle in group_lower:
            return target_group, target_key
    return None


def normalize_attributes(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    unmapped: dict[str, Any] = {}
    for entry in entries:
        attr = entry["attribute"]
        group = entry.get("group") or ""
        value = entry["value"]

        contextual = _route_contextual(attr, group)
        if contextual is not None:
            target_group, target_key = contextual
            grouped.setdefault(target_group, {})[target_key] = value
            continue

        mapping = _ATTR_MAP.get(attr)
        if mapping is None:
            unmapped[f"{group}::{attr}"] = value
            continue
        target_group, target_key = mapping
        grouped.setdefault(target_group, {})[target_key] = value

    if unmapped:
        grouped["_unmapped"] = unmapped
    return grouped
