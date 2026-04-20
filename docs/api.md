# API Reference

All endpoints return JSON. FastAPI also serves the OpenAPI schema at `/openapi.json` and interactive docs at `/docs`.

## Authentication

- Read endpoints (`GET ...`) are public.
- `POST /refresh` requires `X-API-Key: <value>` matching `MOTOSCRAP_API_KEY`.
- If `MOTOSCRAP_API_KEY` is unset, `/refresh` responds with `503 Service Unavailable` so that a forgotten env var cannot turn your deployment into an anonymous scraping proxy.

## GET /health

```json
{ "status": "ok", "version": "0.1.0" }
```

## GET /sources

List the scraper implementations the running image knows about.

```json
[
  { "slug": "1000ps", "name": "1000PS.com", "base_url": "https://www.1000ps.com", "is_active": true }
]
```

## GET /brands?source=1000ps

Brands known to motoscrap for a given source. Brands are discovered as side-effects of model scrapes; an empty list just means you have not scraped anything yet.

## GET /models?source=1000ps&brand=ducati

Models cached for a source. `brand` is optional.

## GET /model-years?source=1000ps&model_external_id=4952

All cached years for a single model.

## GET /specs?source=1000ps&model_external_id=4952&year=2014

Full normalized specs for one year.

```json
{
  "source_slug": "1000ps",
  "brand_name": "Ducati",
  "model_name": "Monster 796",
  "model_external_id": "4952",
  "year": 2014,
  "display_name": "DUCATI MONSTER 796 - 2014",
  "specs": {
    "engine": {
      "bore_mm": 88, "stroke_mm": 66, "power_hp": 87, "power_rpm": 8250,
      "torque_nm": 78, "torque_rpm": 6250, "compression_ratio": 11,
      "displacement_cc": 803, "cooling": "Hava", "cylinders": "2",
      "valves_per_cylinder": "2", "valve_train": "Desmodromik",
      "final_drive": "Zincir"
    },
    "suspension": {
      "front_type": "Baş aşağı teleskopik çatal",
      "front_brand": "Showa",
      "rear_type": "Tek şok",
      "rear_brand": "Showa"
    },
    "chassis": { "frame_material": "Çelik", "frame_type": "Borulu" },
    "brakes_front": { "piston": "Dört piston", "technology": "radyal" },
    "brakes_rear": { "type": "Disk", "piston": "Çift piston" },
    "rider_aids": { "systems": "ABS" },
    "dimensions": {
      "front_tire_width_mm": 120, "front_tire_aspect_ratio": 70, "front_tire_rim_inch": 17,
      "rear_tire_width_mm": 180, "rear_tire_aspect_ratio": 55, "rear_tire_rim_inch": 17,
      "length_mm": 2114, "height_mm": 1079, "wheelbase_mm": 1450,
      "seat_height_mm": 800, "dry_weight_kg": 167, "curb_weight_kg": 187,
      "fuel_tank_l": 15, "license_class": "A"
    }
  },
  "scraped_at": "2026-04-20T09:12:34.567Z"
}
```

`404` if motoscrap has never scraped that year — trigger `/refresh` first.

## GET /search?q=monster&source=1000ps&limit=25

Fuzzy case-insensitive substring search over cached models.

## POST /refresh

Kick off a background scrape task. Returns `202 Accepted` plus a `TaskOut`.

```bash
curl -X POST http://localhost:8000/refresh \
     -H "Content-Type: application/json" \
     -H "X-API-Key: $MOTOSCRAP_API_KEY" \
     -d '{"source": "1000ps", "scope": "model", "model_external_id": "4952"}'
```

Request body:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `source` | string | yes | Source slug |
| `scope` | `"model" \| "brand" \| "all"` | yes | Only `model` is implemented in 0.1.x |
| `model_external_id` | string | if scope=model | |
| `brand_slug` | string | if scope=brand | reserved |
| `model_slug` | string | optional | Hint when the source needs a slug-in-URL |

## GET /tasks/{id}

Poll for task status.

```json
{
  "id": "a81c...",
  "source_slug": "1000ps",
  "scope": "model",
  "params": { "model_external_id": "4952" },
  "status": "succeeded",
  "result": { "years_scraped": [2010, 2011, 2012, 2013, 2014], "errors": [] },
  "error": null,
  "started_at": "...",
  "finished_at": "..."
}
```

`status` is one of `pending`, `running`, `succeeded`, `failed`.
