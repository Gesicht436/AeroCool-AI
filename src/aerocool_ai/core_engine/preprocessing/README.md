# Geospatial Preprocessing & Feature Extraction (`src/aerocool_ai/core_engine/preprocessing/`)

The `preprocessing` submodule bridges multi-resolution Earth observation data and machine learning tensors. It aligns spatial rasters to a unified grid, performs statistical normalization and NoData inpainting, and calculates biophysical and morphometric indices.

---

## 🌟 Quick Primer for Juniors: Why Preprocess Satellite Rasters?

If you are new to satellite remote sensing and GIS data, here is why preprocessing is essential:

### 1. The Multi-Resolution Puzzle
Different satellites look at the Earth with completely different "camera lenses":
- **Sentinel-2** captures visible and near-infrared light at sharp **10-meter** pixels.
- **Landsat 8/9** captures thermal infrared radiation (surface temperature) at **30-meter** pixels.
- **ERA5-Land** gives us atmospheric air temperature and wind speed at coarse **10-kilometer** (0.1°) cells.
- **OpenStreetMap** provides building footprints as geometric vector polygons.

A neural network cannot process images where one channel is a 1000x1000 grid and another is a 10x10 grid.
Our `SpatialAlignmentPipeline` resamples and projects every layer onto the exact same spatial grid (like projecting different overhead transparencies onto the same screen) so that pixel $(i, j)$ represents the exact same physical patch of ground across all layers.

### 2. Key Biophysical Indices in Plain English
- **NDVI (Normalized Difference Vegetation Index)**: Measures **green vegetation density**. Leaves reflect Near-Infrared (NIR) and absorb Red light. High NDVI ($> 0.5$) means dense trees/grass; low NDVI means asphalt or bare dirt.
- **NDBI (Normalized Difference Built-up Index)**: Measures **man-made concrete and buildings**. Concrete reflects SWIR light strongly. High NDBI indicates heavy urban sprawl.
- **Albedo ($\alpha$)**: Measures **surface reflectivity** ("shininess"). White roofs have high albedo ($\sim 0.70$); black asphalt has low albedo ($\sim 0.10$). Low albedo absorbs solar heat.
- **SVF (Sky View Factor)**: Measures **how much open sky is visible from street level**. In deep skyscraper street canyons, SVF is low ($\sim 0.2$), trapping trapped thermal radiation like an oven. In open plazas, SVF is high ($\sim 0.9$).

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/preprocessing/__init__.py)
- **Role**: Module exports.
- **Exports**: `SpatialAlignmentPipeline`, `RasterNormalizer`, `UrbanFeatureExtractor`.

---

### 2. [`spatial_alignment.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/preprocessing/spatial_alignment.py)
- **Role**: Standardizes raster datasets of varying resolutions (10m Sentinel, 30m Landsat, 70m ECOSTRESS, 0.1° ERA5) to a common spatial grid.
- **Key Classes & Methods**:
  - `AlignedGridSpecification`: Defines bounding envelope `(min_lon, min_lat, max_lon, max_lat)`, target grid shape `(H, W)`, and CRS (`EPSG:4326`).
  - `SpatialAlignmentPipeline`:
    - `resample_raster(array, order)`: Uses spline interpolation (`order=1` bilinear for continuous variables like LST/elevation, `order=0` nearest-neighbor for categorical LULC classes).
    - `align_layers(layers, categorical_keys)`: Aligns an arbitrary dictionary of named layers.
    - `stack_feature_tensor(aligned_layers, ordered_keys)`: Stacks aligned 2D feature maps into a multi-channel PyTorch-ready tensor $(C, H, W)$.
- **Usage Example**:
  ```python
  from aerocool_ai.core_engine.preprocessing.spatial_alignment import SpatialAlignmentPipeline

  pipeline = SpatialAlignmentPipeline()
  aligned = pipeline.align_layers({
      "lst": lst_array_30m,
      "lulc": lulc_array_10m,
      "wind": wind_array_10km,
  })
  tensor = pipeline.stack_feature_tensor(aligned, ["lst", "lulc", "wind"])
  print(f"Aligned tensor shape: {tensor.shape}")  # (3, 64, 64)
  ```

---

### 3. [`raster_normalizer.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/preprocessing/raster_normalizer.py)
- **Role**: Statistical feature scaling and spatial gap-filling for cloud-occluded or missing satellite pixels.
- **Key Classes & Methods**:
  - `ChannelStatistics`: Tracks per-channel mean, std, min, max, 25th quantile, and 75th quantile.
  - `RasterNormalizer`: Supports `minmax`, `zscore`, and `robust` (Interquartile Range) normalizations across 2D, 3D $(C, H, W)$, and 4D $(N, C, H, W)$ tensors.
    - `fit()`, `transform()`, `fit_transform()`, `inverse_transform()`.
  - `inpaint_nodata(raster, nodata_mask, method)`: Spatial NoData repair using **Euclidean Distance Transform (EDT)** nearest-neighbor indexing with optional Gaussian boundary smoothing.
- **Usage Example**:
  ```python
  from aerocool_ai.core_engine.preprocessing.raster_normalizer import RasterNormalizer

  # Inpaint missing cloud pixels
  clean_lst = RasterNormalizer.inpaint_nodata(gappy_lst_array)

  # Scale features to [0, 1]
  normalizer = RasterNormalizer(method="minmax")
  normed_tensor = normalizer.fit_transform(feature_tensor)
  ```

---

### 4. [`feature_extractor.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/preprocessing/feature_extractor.py)
- **Role**: Computes essential thermodynamic and biophysical indices for microclimate modeling.
- **Key Indicators & Mathematical Formulations**:

1. **Normalized Difference Vegetation Index (NDVI)**:
   $$\text{NDVI} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$$
2. **Normalized Difference Built-Up Index (NDBI)**:
   $$\text{NDBI} = \frac{\text{SWIR} - \text{NIR}}{\text{SWIR} + \text{NIR}}$$
3. **Normalized Difference Water Index (NDWI)**:
   $$\text{NDWI} = \frac{\text{Green} - \text{NIR}}{\text{Green} + \text{NIR}}$$
4. **Broadband Surface Albedo ($\alpha$) (Liang, 2001 Multispectral Formula)**:
   $$\alpha = 0.356 B_2 + 0.130 B_4 + 0.373 B_8 + 0.085 B_{11} + 0.072 B_{12} - 0.0018$$
5. **Fractional Vegetation Cover ($\text{FVC} / f_v$)**:
   $$\text{FVC} = \left( \frac{\text{NDVI} - \text{NDVI}_{\text{soil}}}{\text{NDVI}_{\text{veg}} - \text{NDVI}_{\text{soil}}} \right)^2 \quad (\text{where } \text{NDVI}_{\text{soil}}=0.05, \text{NDVI}_{\text{veg}}=0.70)$$
6. **Surface Thermal Emissivity ($\varepsilon$) (Sobrino et al. NDVI Threshold Method)**:
   $$\varepsilon = \varepsilon_v \cdot \text{FVC} + \varepsilon_s \cdot (1 - \text{FVC}) + 0.004 \cdot \text{FVC} \cdot (1 - \text{FVC})$$
7. **Sky View Factor ($\text{SVF}$)** (Street Canyon Model):
   $$\text{SVF} = \cos\left( \arctan\left( \frac{2 \cdot H_{\text{eff}}}{W_{\text{street}}} \right) \right)$$

- **Usage Example**:
  ```python
  from aerocool_ai.core_engine.preprocessing.feature_extractor import UrbanFeatureExtractor

  extractor = UrbanFeatureExtractor()
  feat = extractor.extract_features(
      blue=b2, green=b3, red=b4, nir=b8, swir1=b11, swir2=b12,
      building_height=height_grid,
      plan_area_fraction=plan_area_grid
  )
  print(f"Broadband Albedo mean: {feat.albedo.mean():.3f}, FVC mean: {feat.fvc.mean():.3f}")
  ```
