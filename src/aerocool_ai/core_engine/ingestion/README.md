# Data Ingestion Submodule (`src/aerocool_ai/core_engine/ingestion/`)

The `ingestion` submodule handles automated multi-source geospatial and meteorological data collection, cloud-screening, radiometric calibration, and spatial querying.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/ingestion/__init__.py)
- **Role**: Module exports and public interface definition.
- **Exports**: `LandsatLSTCollector`, `ECOSTRESSCollector`, `SentinelLULCCollector`, `ERA5MeteoCollector`, `OSMMorphologyCollector`.

---

### 2. [`gee_landsat_collector.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/ingestion/gee_landsat_collector.py)
- **Role**: Ingests Landsat 8 and Landsat 9 Thermal Infrared Sensor (TIRS) data via the Google Earth Engine (GEE) Python API.
- **Key Classes & Data Structures**:
  - `LSTRasterResult`: Container holding the calibrated temperature array (in °C), affine transform tuple, CRS (`EPSG:4326`), bounding box, timestamp, cloud cover percentage, and metadata.
  - `LandsatLSTCollector`: The client managing GEE authentication (Service Account or OAuth project ID), image collection filtering (`LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2`), and cloud masking.
- **Physical Radiometric Calibration**:
  $$\text{LST}\,(^\circ\text{C}) = (\text{ST\_B10} \times 0.00341802 + 149.0) - 273.15$$
- **Cloud & Shadow Screening**:
  Decodes Landsat `QA_PIXEL` bitmask (Bit 1: Dilated Cloud, Bit 3: Cloud, Bit 4: Cloud Shadow).
- **Strict Authentication & Verification**: In Strict Error Mode, raises explicit `RuntimeError` if Earth Engine credentials (`GEE_SERVICE_ACCOUNT` / `GEE_PROJECT_ID`) are not authenticated.
- **Dynamic Scale Adaptation (`effective_scale`)**:
  To protect against Earth Engine's compute limit of 262,144 pixels per `sampleRectangle` call, the collector automatically calculates an optimal target scale:
  $$\text{effective\_scale} = \max\left(\text{resolution\_meters}, \frac{\max(\text{width\_m}, \text{height\_m})}{256}\right)$$
  This guarantees that large municipal bounding boxes (e.g. Delhi NCR, 16 km $\times$ 16 km) download smoothly in 1-2 seconds without pixel-overflow errors.
- **Usage Example**:
  ```python
  from aerocool_ai.core_engine.ingestion.gee_landsat_collector import LandsatLSTCollector

  collector = LandsatLSTCollector()
  bbox = (77.10, 28.58, 77.26, 28.72)  # Delhi NCR
  result = collector.fetch_lst_aoi(bbox, "2026-05-01", "2026-06-30", max_cloud_cover=20.0)
  print(f"LST Grid Shape: {result.data.shape}, Mean Temp: {result.data.mean():.2f} °C")
  ```

---

### 3. [`ecostress_collector.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/ingestion/ecostress_collector.py)
- **Role**: Collects high-resolution (70m) diurnal Land Surface Temperature from NASA's ECOSTRESS instrument aboard the International Space Station (ISS).
- **Key Classes & Data Structures**:
  - `ECOSTRESSObservation`: Stores LST (°C), quality control mask, acquisition timestamp, local solar time (in decimal hours), spatial bounds, and granule ID.
  - `ECOSTRESSCollector`: Simulates or queries diurnal overpasses (morning 09:00, solar noon 13:00, afternoon peak 16:00, nocturnal 22:00) to capture urban thermal inertia and nocturnal heat retention.
- **Usage Example**:
  ```python
  from aerocool_ai.core_engine.ingestion.ecostress_collector import ECOSTRESSCollector

  collector = ECOSTRESSCollector()
  passes = collector.fetch_diurnal_passes((-74.02, 40.70, -73.95, 40.78), "2026-07-15")
  for p in passes:
      print(f"Pass at {p.local_solar_time_hours:.1f}h | Mean Temp: {p.data.mean():.2f} °C")
  ```

---

### 4. [`sentinel_lulc_collector.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/ingestion/sentinel_lulc_collector.py)
- **Role**: Ingests Sentinel-2 Level-2A surface reflectance bands and 10m Land Use / Land Cover (LULC) categorical data (ESA WorldCover / Dynamic World).
- **Key Classes & Data Structures**:
  - `LULCClass` (IntEnum): Standardized 10m classes (Water: 10, Trees: 20, Shrubland: 30, Grassland: 40, Cropland: 50, Built-up High Density: 60, Built-up Residential: 61, Bare Soil: 70, Roads/Impervious: 90).
  - `SentinelLULCResult`: Stores 6 optical reflectance bands (`blue`, `green`, `red`, `nir`, `swir1`, `swir2`), `lulc_class` grid, cloud mask, transform, and CRS.
  - `SentinelLULCCollector`: Fetches multispectral composites and categorical LULC rasters with automatic service account authentication and dynamic scale alignment.
- **Usage Example**:
  ```python
  from aerocool_ai.core_engine.ingestion.sentinel_lulc_collector import SentinelLULCCollector

  collector = SentinelLULCCollector()
  result = collector.fetch_multispectral_and_lulc((77.10, 28.58, 77.26, 28.72), "2026-05-01", "2026-06-30")
  print(f"NIR band shape: {result.nir.shape}, Built-up pixels: {(result.lulc_class == 60).sum()}")
  ```

---

### 5. [`era5_meteo_collector.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/ingestion/era5_meteo_collector.py)
- **Role**: Ingests hourly atmospheric boundary conditions from ECMWF ERA5-Land reanalysis via Copernicus CDS API (`cdsapi`).
- **Key Classes & Data Structures**:
  - `ERA5MeteoGrid`: Grid container storing 2m Air Temperature ($T_{2m}$), Downward Shortwave Solar Radiation ($R_{sw\downarrow}$), Downward Longwave Thermal Radiation ($R_{lw\downarrow}$), 10m Wind Speed ($U_{10}$), Relative Humidity ($\text{RH}$), and Surface Pressure ($P_s$).
  - `ERA5MeteoCollector`: Computes meteorological fields and calculates relative humidity via the **Magnus-Tetens** formulation:
    $$\text{RH} = 100 \times \frac{\exp\left(\frac{17.625 \cdot T_{\text{dew}}}{243.04 + T_{\text{dew}}}\right)}{\exp\left(\frac{17.625 \cdot T_{\text{air}}}{243.04 + T_{\text{air}}}\right)}$$
- **Usage Example**:
  ```python
  from datetime import datetime
  from aerocool_ai.core_engine.ingestion.era5_meteo_collector import ERA5MeteoCollector

  collector = ERA5MeteoCollector()
  meteo = collector.fetch_hourly_meteo((77.10, 28.58, 77.26, 28.72), datetime(2026, 6, 15, 12, 0))
  print(f"Solar radiation: {meteo.r_sw_down.mean():.1f} W/m², Air temp: {meteo.t2m_celsius.mean():.1f} °C")
  ```

---

### 6. [`osm_morphology_collector.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/ingestion/osm_morphology_collector.py)
- **Role**: Queries OpenStreetMap (OSM) vector building footprints and street networks via OSMnx and Overpass API to compute 3D urban canopy parameters.
- **Key Classes & Data Structures**:
  - `UrbanMorphologyGrid`: Stores rasterized mean building heights ($H_{\text{mean}}$), maximum building heights ($H_{\text{max}}$), Building Plan Area Fraction ($\lambda_p$), Aerodynamic Roughness Length ($z_0$), and Frontal Area Index ($\lambda_f$).
  - `OSMMorphologyCollector`: Parses building storey counts (`building:levels` $\times 3.2\text{m}$) and heights.
- **High-Speed Vectorized Rasterization**:
  Instead of slow row-by-row DataFrame iteration, the collector uses vectorized NumPy index mapping (`np.add.at` and `np.maximum.at`) to project tens of thousands of building polygons onto computational grids in under 15 milliseconds.
- **Aerodynamic Roughness Formulation (Grimmond & Oke, 1999)**:
  $$z_0 = 0.10 \times H_{\text{mean}} \times \sqrt{\lambda_p}$$
- **Usage Example**:
  ```python
  from aerocool_ai.core_engine.ingestion.osm_morphology_collector import OSMMorphologyCollector

  collector = OSMMorphologyCollector()
  morph = collector.fetch_morphology((77.10, 28.58, 77.26, 28.72), grid_shape=(256, 292))
  print(f"Max building height: {morph.building_height_max.max():.1f} m, Mean density lambda_p: {morph.plan_area_fraction.mean():.2f}")
  ```
