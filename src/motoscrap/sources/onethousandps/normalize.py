from __future__ import annotations

from typing import Any

# Maps 1000ps's stable `translationKey` values to motoscrap's locale-invariant
# English keys. The translation key is the same across every locale the source
# renders in, so the normaliser works regardless of which locale was scraped.
_ATTR_MAP: dict[str, tuple[str, str]] = {
    # Engine & drivetrain (attrgroup#1)
    "bikekat#attr#3": ("engine", "cylinders"),
    "bikekat#attr#5": ("engine", "valves_per_cylinder"),
    "bikekat#attr#6": ("engine", "valve_train"),
    "bikekat#attr#7": ("engine", "cooling"),
    "bikekat#attr#8": ("engine", "lubrication"),
    "bikekat#attr#9": ("engine", "displacement_cc"),
    "bikekat#attr#10": ("engine", "bore_mm"),
    "bikekat#attr#11": ("engine", "stroke_mm"),
    "bikekat#attr#12": ("engine", "power_hp"),
    "bikekat#attr#13": ("engine", "power_rpm"),
    "bikekat#attr#14": ("engine", "torque_nm"),
    "bikekat#attr#15": ("engine", "torque_rpm"),
    "bikekat#attr#16": ("engine", "compression_ratio"),
    "bikekat#attr#17": ("engine", "fuel_system"),
    "bikekat#attr#18": ("engine", "injectors_per_cylinder"),
    "bikekat#attr#19": ("engine", "throttle_body_diameter_mm"),
    "bikekat#attr#20": ("engine", "starter"),
    "bikekat#attr#21": ("engine", "clutch_type"),
    "bikekat#attr#22": ("engine", "ignition"),
    "bikekat#attr#23": ("engine", "final_drive"),
    "bikekat#attr#25": ("engine", "gearbox_type"),
    "bikekat#attr#26": ("engine", "gear_count"),
    "bikekat#attr#74": ("engine", "a2_restrictable"),
    # Front suspension (attrgroup#2)
    "bikekat#attr#27": ("suspension", "front_type"),
    "bikekat#attr#28": ("suspension", "front_technology"),
    "bikekat#attr#29": ("suspension", "front_brand"),
    "bikekat#attr#30": ("suspension", "front_fork_tube_diameter_mm"),
    "bikekat#attr#31": ("suspension", "front_travel_mm"),
    "bikekat#attr#32": ("suspension", "front_adjustment"),
    # Rear suspension (attrgroup#8)
    "bikekat#attr#33": ("suspension", "rear_type"),
    "bikekat#attr#34": ("suspension", "rear_shock"),
    "bikekat#attr#35": ("suspension", "rear_linkage"),
    "bikekat#attr#36": ("suspension", "rear_brand"),
    "bikekat#attr#37": ("suspension", "rear_travel_mm"),
    "bikekat#attr#38": ("suspension", "rear_adjustment"),
    "bikekat#attr#78": ("suspension", "rear_material"),
    # Chassis (attrgroup#7)
    "bikekat#attr#39": ("chassis", "frame_material"),
    "bikekat#attr#40": ("chassis", "frame_type"),
    "bikekat#attr#76": ("chassis", "rake_deg"),
    "bikekat#attr#77": ("chassis", "trail_mm"),
    # Front brakes (attrgroup#3)
    "bikekat#attr#41": ("brakes_front", "type"),
    "bikekat#attr#42": ("brakes_front", "disc_diameter_mm"),
    "bikekat#attr#43": ("brakes_front", "piston"),
    "bikekat#attr#44": ("brakes_front", "mount"),
    "bikekat#attr#45": ("brakes_front", "actuation"),
    "bikekat#attr#46": ("brakes_front", "technology"),
    "bikekat#attr#47": ("brakes_front", "brand"),
    # Rear brakes (attrgroup#9)
    "bikekat#attr#48": ("brakes_rear", "type"),
    "bikekat#attr#49": ("brakes_rear", "disc_diameter_mm"),
    "bikekat#attr#50": ("brakes_rear", "piston"),
    "bikekat#attr#51": ("brakes_rear", "mount"),
    "bikekat#attr#52": ("brakes_rear", "brand"),
    # Rider aids (attrgroup#4)
    "bikekat#attr#53": ("rider_aids", "systems"),
    # Dimensions & weights (attrgroup#5)
    "bikekat#attr#54": ("dimensions", "front_tire_width_mm"),
    "bikekat#attr#55": ("dimensions", "front_tire_aspect_ratio"),
    "bikekat#attr#56": ("dimensions", "front_tire_rim_inch"),
    "bikekat#attr#57": ("dimensions", "rear_tire_width_mm"),
    "bikekat#attr#58": ("dimensions", "rear_tire_aspect_ratio"),
    "bikekat#attr#59": ("dimensions", "rear_tire_rim_inch"),
    "bikekat#attr#60": ("dimensions", "length_mm"),
    "bikekat#attr#61": ("dimensions", "width_mm"),
    "bikekat#attr#62": ("dimensions", "height_mm"),
    "bikekat#attr#63": ("dimensions", "wheelbase_mm"),
    "bikekat#attr#64": ("dimensions", "seat_height_mm"),
    "bikekat#attr#65": ("dimensions", "seat_height_max_mm"),
    "bikekat#attr#66": ("dimensions", "dry_weight_kg"),
    "bikekat#attr#67": ("dimensions", "curb_weight_kg"),
    "bikekat#attr#68": ("dimensions", "dry_weight_with_abs_kg"),
    "bikekat#attr#69": ("dimensions", "curb_weight_with_abs_kg"),
    "bikekat#attr#70": ("dimensions", "fuel_tank_l"),
    "bikekat#attr#71": ("dimensions", "top_speed_kph"),
    "bikekat#attr#72": ("dimensions", "license_class"),
    "bikekat#attr#75": ("dimensions", "lowerable"),
    "bikekat#attr#80": ("dimensions", "range_km"),
    "bikekat#attr#81": ("dimensions", "battery_voltage_v"),
    "bikekat#attr#82": ("dimensions", "battery_capacity_ah"),
    "bikekat#attr#83": ("dimensions", "battery_removable"),
    "bikekat#attr#84": ("dimensions", "co2_combined"),
    "bikekat#attr#85": ("dimensions", "fuel_consumption_extraurban"),
    "bikekat#attr#86": ("dimensions", "fuel_consumption_urban"),
    "bikekat#attr#87": ("dimensions", "fuel_consumption_combined"),
    "bikekat#attr#88": ("dimensions", "noise_static_db"),
    "bikekat#attr#89": ("dimensions", "noise_above_95db"),
    "bikekat#attr#90": ("dimensions", "charge_plug"),
    "bikekat#attr#91": ("dimensions", "max_charge_power"),
    "bikekat#attr#92": ("dimensions", "regen_braking"),
    "bikekat#attr#93": ("dimensions", "battery_performance_kwh"),
    "bikekat#attr#94": ("dimensions", "euro_standard"),
    "bikekat#attr#95": ("dimensions", "payload_kg"),
    "bikekat#attr#96": ("dimensions", "gross_weight_max_kg"),
    "bikekat#attr#97": ("dimensions", "service_interval_km"),
    "bikekat#attr#98": ("dimensions", "ground_clearance_mm"),
}


def normalize_attributes(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    unmapped: dict[str, Any] = {}
    for entry in entries:
        attribute_key = entry.get("attribute_key")
        value = entry["value"]

        mapping = _ATTR_MAP.get(str(attribute_key)) if attribute_key else None
        if mapping is None:
            label = entry.get("attribute") or str(attribute_key)
            unmapped[str(label)] = value
            continue
        target_group, target_key = mapping
        grouped.setdefault(target_group, {})[target_key] = value

    if unmapped:
        grouped["_unmapped"] = unmapped
    return grouped
