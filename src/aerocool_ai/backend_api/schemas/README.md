# Pydantic API Schemas (`src/aerocool_ai/backend_api/schemas/`)

This directory contains Pydantic v2 data transfer objects (DTOs) and serialization schemas for request validation and response formatting.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/__init__.py)
- **Role**: Exports public request and response schemas.

---

### 2. [`hotspot_schema.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/hotspot_schema.py)
- **Role**: Defines GeoJSON-compliant structures for Urban Heat Island (UHI) hotspot detection.
- **Key Schemas**:
  - `HotspotDetectionRequest`: Input bounding box `bbox`, date range, target satellite sensor (`Landsat-8/9`, `ECOSTRESS`, `Sentinel-2`), minimum temperature anomaly threshold (°C), and spatial resolution.
  - `GeoJSONGeometry`: RFC 7946 geometry (`Polygon`, `Point`, `MultiPolygon`).
  - `HotspotProperties`: Thermal properties for an individual hotspot cell (LST, UHI intensity anomaly, regional baseline mean, Heat Vulnerability Index, dominant heating driver, albedo, FVC, building density, SVF, severity level).
  - `HotspotFeature`: Standard GeoJSON Feature containing geometry and properties.
  - `HotspotFeatureCollection`: GeoJSON FeatureCollection returning array of hotspot features and execution metadata.

---

### 3. [`scenario_request.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/scenario_request.py)
- **Role**: Defines simulation payload and response models.
- **Key Schemas**:
  - `SimulationRunRequest`: Scenario name, bounding box `bbox`, strategy type (`green_roof`, `cool_roof`, `urban_canopy`, `cool_pavement`, `permeable_pavement`, `multi_strategy`), target conversion fraction, capital budget ($), and custom $\Delta \alpha$ / $\Delta f_v$ overrides.
  - `SimulationRunResponse`: Computed thermodynamic results ($\Delta T_{\text{LST}}$, $\Delta T_{\text{air}}$), modified area ($\text{m}^2$), capital cost ($), annual electricity saved ($\text{kWh}$), avoided $\text{CO}_2$ emissions (tons), financial payback (years), UTCI stress category shift, and GeoJSON result layer.
  - `ScenarioItemResponse`: Summary model for historical scenario listing.

---

### 4. [`optimization_response.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/backend_api/schemas/optimization_response.py)
- **Role**: Defines spatial optimization and Pareto efficiency schemas.
- **Key Schemas**:
  - `OptimizationAllocationRequest`: Target bounding box, investment budget, permitted intervention techniques, and social vulnerability weighting toggle.
  - `AllocatedParcelSchema`: Metadata for a specific parcel selected for cooling intervention (grid coordinates, approximate latitude/longitude, assigned strategy, area, cost, expected $\Delta T$, priority rank).
  - `OptimizationAllocationResponse`: Total spent, remaining budget, allocated parcel lists, strategy breakdown counts, and full GeoJSON allocation map.
  - `ParetoPointSchema` & `ParetoFrontierResponse`: Series of scenario points mapping investment budget steps to temperature reductions, highlighting the recommended knee-point budget.
