# Filters

OData queries use an OData `$filter` expression. The
[`FilterBuilder`](reference/odata.md) assembles one safely (escaping string
literals, formatting dates, choosing attribute types) and joins every condition
with a logical `and`. A raw escape hatch is always available.

```python
from cdse import FilterBuilder

flt = (
    FilterBuilder()
    .collection("SENTINEL-2")
    .name_contains("MSIL2A")
    .acquired_between("2024-05-01", "2024-05-08")
    .attribute("cloudCover", "le", 20.0)
    .online()
)
products = client.odata.products.search(flt)
```

## Available conditions

| Method | Produces |
| --- | --- |
| `.collection(name)` | `Collection/Name eq '...'` |
| `.name(value)` | `Name eq '...'` |
| `.name_contains(value)` | `contains(Name,'...')` |
| `.online(value=True)` | `Online eq true` |
| `.acquired_between(start, end)` | `ContentDate/Start ge ... and le ...` |
| `.published_between(start, end)` | `PublicationDate ge ... and le ...` |
| `.intersects(wkt)` | `OData.CSC.Intersects(area=geography'SRID=4326;...')` |
| `.attribute(name, op, value)` | typed `Attributes/.../any(...)` |
| `.deleted_between(start, end)` | `DeletionDate ...` (DeletedProducts) |
| `.deletion_cause(cause)` | `DeletionCause eq '...'` (DeletedProducts) |
| `.raw(expression)` | the expression verbatim |

Dates accept `datetime`, `date`, or anything those construct from; naive
datetimes are treated as UTC.

## Attributes

`.attribute(name, operator, value)` infers the OData attribute type from the
Python value: `int` → Integer, `float` → Double, `str` → String, `datetime`/`date`
→ DateTimeOffset. Operators are `eq`, `ne`, `lt`, `le`, `gt`, `ge`.

```python
FilterBuilder().attribute("cloudCover", "le", 40.0)       # Double
FilterBuilder().attribute("orbitNumber", "eq", 12)        # Integer
FilterBuilder().attribute("productType", "eq", "S2MSI2A") # String
```

## Regions of interest (ROIs)

Pass a WKT geometry in EPSG:4326 to `.intersects()`. Polygon rings must be
closed (first point equals last).

```python
FilterBuilder().intersects("POLYGON((4 50, 5 50, 5 51, 4 51, 4 50))")
FilterBuilder().intersects("POINT(4 50)")
```

### Multiple ROIs

Because the builder joins with `and`, calling `.intersects()` twice means
"intersects A **and** B" (an empty result for disjoint areas). For "A **or** B",
either use one `MULTIPOLYGON`:

```python
multi = "MULTIPOLYGON(((4 50,5 50,5 51,4 51,4 50)),((10 45,11 45,11 46,10 46,10 45)))"
FilterBuilder().collection("SENTINEL-2").intersects(multi)
```

or build a parenthesised OR group with `.raw()`:

```python
a = "OData.CSC.Intersects(area=geography'SRID=4326;POLYGON((4 50,5 50,5 51,4 51,4 50))')"
b = "OData.CSC.Intersects(area=geography'SRID=4326;POLYGON((10 45,11 45,11 46,10 46,10 45))')"
FilterBuilder().collection("SENTINEL-2").raw(f"({a} or {b})")
```

The same `$filter` grammar is accepted by the
[Subscriptions](usage.md#subscriptions) `FilterParam`, so ROIs work there too.

## Ordering

```python
from cdse import build_orderby

client.odata.products.search(flt, order_by=build_orderby("ContentDate/Start", "desc"))
```

## STAC filters

STAC search uses its own parameters (`collections`, `bbox`, `datetime`,
`intersects`) plus the CQL2 filter extension:

```python
client.stac.search(
    collections=["sentinel-2-l2a"],
    filter={"op": "<=", "args": [{"property": "eo:cloud_cover"}, 20]},
    filter_lang="cql2-json",
)
```
