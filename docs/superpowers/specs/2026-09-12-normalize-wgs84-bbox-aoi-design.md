# Normalize WGS84 Bounding-Box AOIs

## Purpose

Provide a small public API that turns a WGS84 bounding box into a validated
Shapely polygon for downstream Sentinel-2 requests.

## Public API

`sentinel2_ingest.aoi.normalize_bbox(west, south, east, north) -> Polygon`

The function accepts four finite numeric longitude/latitude bounds in WGS84.
Its docstring documents the positional inputs, the returned Shapely `Polygon`,
EPSG:4326 coordinate semantics, validation rules, and `InvalidAOIError`.

## Validation and geometry

- Longitude bounds must satisfy `-180 <= west < east <= 180`.
- Latitude bounds must satisfy `-90 <= south < north <= 90`.
- Equal bounds are rejected as zero-area boxes.
- Reversed longitude bounds are rejected, including antimeridian-crossing
  boxes (`west > east`); splitting a box at the antimeridian is out of scope.
- Reversed latitude bounds, out-of-range values, non-numeric values, and
  non-finite values are rejected.
- Every invalid input raises the existing public `InvalidAOIError` with an
  actionable detail message.
- A valid box becomes a closed, rectangular Shapely `Polygon` whose coordinate
  order is `(longitude, latitude)`. Shapely geometries do not intrinsically
  store a CRS, so EPSG:4326 is the documented coordinate contract.

## Package integration

The implementation lives in `sentinel2_ingest.aoi`. Shapely is added as a
runtime dependency. The function remains module-scoped and is not re-exported
from `sentinel2_ingest.__init__`.

## Tests

Tests assert the returned object is a valid `Polygon`, has the expected
rectangle coordinates and area, and covers valid edge-of-range bounds.
Parameterized invalid-input tests cover reversed bounds, antimeridian
crossing, longitude/latitude range violations, zero-area boxes, non-numeric
values, and non-finite values. Import coverage verifies the module-scoped
public API remains available.
