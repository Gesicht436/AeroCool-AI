# AeroCool-AI: Project Dependencies

This document lists all Python dependencies utilized across the **AeroCool-AI** system, categorized by module, with detailed explanations of their purpose.

---

## 1. Geospatial Data Ingestion (Module 1)

These libraries are used by **Harsh & Shaurya** to connect to satellite and weather data servers, query spatial scenes, and download raw data.

* **`pystac-client`**
  * *What it does:* Query engines that implement SpatioTemporal Asset Catalog (STAC) specifications.
  * *Why we use it:* Allows querying remote-sensing catalogs (e.g., USGS Landsat, ESA Sentinel on AWS/Microsoft Planetary Computer) to locate cloud-free image granules over our target urban region.
* **`sentinelsat`**
  * *What it does:* Python API wrapper for the Copernicus Open Access Hub.
  * *Why we use it:* Programmatic querying and downloading of high-resolution Sentinel-2 Land Use/Land Cover (LULC) bands.
* **`earthengine-api`**
  * *What it does:* Official client library for Google Earth Engine (GEE).
  * *Why we use it:* Offers cloud-computation resources for pre-filtering large Landsat-8 collections and exporting processed surface temperature maps.
* **`cdsapi`**
  * *What it does:* Copernicus Climate Data Store API client.
  * *Why we use it:* Fetches historical and forecast weather variables (ERA5 atmospheric temperatures, wind velocities, and relative humidity) for our project site.

---

## 2. Spatial Alignment & Processing (Module 1 & 2)

These tools align different spatial grids (e.g., Landsat at 30m, Sentinel at 10m, and ERA5 at ~30km) onto a standardized spatial resolution.

* **`rasterio` & `GDAL`**
  * *What it does:* Core read, write, and transformation engine for raster formats (GeoTIFFs).
  * *Why we use it:* Allows low-level access to image pixels, metadata headers, bounding boxes, and projections.
* **`geopandas` & `fiona`**
  * *What it does:* Extends `pandas` dataframes to handle spatial vector objects (Points, Lines, Polygons).
  * *Why we use it:* Handles urban vectors like building outlines, parks, roads, and municipal administrative limits.
* **`rioxarray`**
  * *What it does:* Geospatial extension for `xarray` powered by `rasterio`.
  * *Why we use it:* Crucial for multi-dimensional coordinate mapping. It handles spatial clipping, scaling, reprojecting (converting coordinate references), and resampling raster grids to a unified **30m target pixel grid**.
* **`rasterstats`**
  * *What it does:* Computes zonal stats of raster layers based on vector geometries.
  * *Why we use it:* Calculates average values (e.g., average surface albedo or vegetation index) inside specific urban zones or neighborhoods.
* **`shapely` & `pyproj`**
  * *What it does:* Core cartographic coordinate system transformations and planar geometric functions.
  * *Why we use it:* Buffer generation, checking polygon overlaps, and converting coordinate degrees into metric projections (UTM).
* **`osmnx` & `networkx`**
  * *What it does:* Downloads street networks and urban morphology maps from OpenStreetMap.
  * *Why we use it:* Creates structural graphs of urban layouts to analyze building heights, orientation, and dense configurations.

---

## 3. Analytical Compute & Feature Engineering (Module 2)

These packages are used by **Shubham** to compute physical and spatial features (like NDVI, NDBI, Albedo, and SVF) and export the final dataset.

* **`numpy`**
  * *What it does:* Fundamental multi-dimensional array math library.
  * *Why we use it:* Vectorized computing for thermal indices, index formulas (NDVI/NDBI), and rapid coordinate grid lookups.
* **`pandas`**
  * *What it does:* Dataframe structures for structured tabular data.
  * *Why we use it:* Combines spatial grid values into a 2D tabular feature matrix (one row per 30m pixel) ready to feed into ML training.
* **`scipy`**
  * *What it does:* Science-focused equations, interpolation, and signal processing.
  * *Why we use it:* Spatial interpolation to estimate values between sparse points and running numerical physical gradients.
* **`scikit-image`**
  * *What it does:* Image processing library for structural analysis.
  * *Why we use it:* Implements morphological erosion, dilation, and structural shadow kernels required to calculate the **Sky View Factor (SVF)**.

---

## 4. Machine Learning & Physical Modeling (Module 3)

These tools are used by the **Team Leader** to build the Physics-Informed ML engine predicting Land Surface Temperature (LST).

* **`torch` (PyTorch with CUDA)**
  * *What it does:* Modern deep learning framework with auto-differentiation capabilities.
  * *Why we use it:* Builds the **Physics-Informed Neural Network (PINN)**. Auto-grad allows backpropagating physical loss terms (e.g., thermodynamic energy balance constraints) directly into weights.
* **`xgboost`**
  * *What it does:* Highly optimized gradient boosted decision trees.
  * *Why we use it:* Models non-linear LST relations and computes feature rankings to find out exactly which urban factors (e.g., low albedo vs. high building density) contribute the most to heat islands.
* **`scikit-learn`**
  * *What it does:* Standard machine learning toolset.
  * *Why we use it:* Standardizing and normalizing data matrices (StandardScaler, MinMaxScaler), regression scoring metrics (RMSE, R²), and splitting datasets into spatial cross-validation folds.
* **`tensorboard`**
  * *What it does:* Visualization tool for tracking ML training parameters.
  * *Why we use it:* Tracks PINN training, plotting validation accuracy, and physics-loss curves in real time.
* **`tqdm`**
  * *What it does:* Command-line progress indicator.
  * *Why we use it:* Tracks dataset generation steps and model training loops.

---

## 5. Optimization & Cooling Models (Module 4)

Used by the **Team Leader** to find the absolute best mitigation designs under budget constraints.

* **`optuna`**
  * *What it does:* State-of-the-art Bayesian and Genetic global optimization search framework.
  * *Why we use it:* Finds the most cost-effective placement of cooling features (e.g., planting trees vs painting roofs white) to maximize temperature drop in an area.
* **`natcap.invest`**
  * *What it does:* Software suite developed by Stanford/WWF to model ecosystem services.
  * *Why we use it:* Leverages the validated physical equations of the **InVEST Urban Cooling model** to compare predictions against our neural network predictions.

---

## 6. Interactive Interface & Presentation (Module 4 UI)

Used by **Shubham** to render the results into a gorgeous, dashboard interface.

* **`streamlit`**
  * *What it does:* Web-app builder for ML and data science tools.
  * *Why we use it:* Powers our scenario simulator dashboard without requiring full-stack JS frameworks.
* **`streamlit-folium` & `folium`**
  * *What it does:* Renders interactive maps inside Streamlit based on Leaflet.
  * *Why we use it:* Allows team members and judges to pan, zoom, click on hotspots, and paint intervention zones.
* **`pydeck`**
  * *What it does:* High-performance WebGL-powered 3D spatial mapping interface.
  * *Why we use it:* Visualizes building density and 3D urban canopy temperature impacts.
* **`plotly`**
  * *What it does:* Interactive chart visualization library.
  * *Why we use it:* Interactive driver analysis plots and cooling curve plots for scenarios.
* **`matplotlib` & `seaborn`**
  * *What it does:* Standard charting tools.
  * *Why we use it:* Used to generate static thermodynamic reports and distribution charts.

---

## 7. Tooling & Development QA

Used by all team members to ensure code quality.

* **`pytest`**: Python unit and integration testing suite.
* **`ruff`**: Next-generation linter and formatter used to maintain code style and catch bugs.
* **`ipykernel`**: Kernel connection supporting exploratory Jupyter Notebooks.
