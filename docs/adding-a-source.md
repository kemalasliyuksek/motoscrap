# Adding a new source

A source is a Python class that knows how to talk to one motorcycle database (1000ps.com, bikez.com, etc.) and translate its data into motoscrap's DTOs.

## 1. Create the package

```
src/motoscrap/sources/<slug>/
├── __init__.py       # Register the class
├── source.py         # Subclass of BaseSource
├── parser.py         # Pure functions that turn HTML/JSON into DTOs
└── urls.py           # URL builders
```

## 2. Subclass `BaseSource`

```python
from motoscrap.sources.base import BaseSource, BrandDTO, ModelDTO, SpecsDTO

class MySource(BaseSource):
    slug = "example"
    name = "Example.com"
    base_url = "https://example.com"

    async def list_brands(self): ...
    async def list_models(self, brand): ...
    async def list_model_years(self, model): ...
    async def fetch_specs(self, model, year): ...
```

## 3. Register it

In `src/motoscrap/sources/<slug>/__init__.py`:

```python
from motoscrap.sources import registry
from motoscrap.sources.<slug>.source import MySource

registry.register(MySource)
```

The top-level `sources` package auto-imports every subpackage on startup, so your class becomes available to the API and CLI immediately.

## 4. Write tests

Save a representative HTML (or JSON) response under `tests/fixtures/<slug>/` and lock its parsed output down with pytest.

```python
def test_parser(fixtures_dir):
    html = (fixtures_dir / "<slug>" / "example.html").read_text()
    specs = parser.parse_specs(html)
    assert specs.year == 2020
    assert specs.grouped["engine"]["displacement_cc"] == 650
```

## 5. Normalize

motoscrap stores specs under stable English keys. Translate the source's native attribute names into the shared shape:

```
engine.bore_mm, engine.stroke_mm, engine.power_hp, engine.torque_nm,
engine.displacement_cc, engine.cooling,
suspension.front_type, suspension.rear_type,
brakes_front.type, brakes_front.piston,
brakes_rear.type, brakes_rear.piston,
dimensions.length_mm, dimensions.wheelbase_mm, dimensions.dry_weight_kg,
dimensions.fuel_tank_l, ...
```

Anything unmapped goes into `specs["_unmapped"]` so nothing is ever silently lost.

## 6. Be a good citizen

- Check the source's `robots.txt` and only scrape what is allowed.
- Respect the global rate limit (`HTTP_RATE_LIMIT_PER_SEC`).
- Include a contact URL in `HTTP_USER_AGENT`.
- Don't hammer a site; cache aggressively.
