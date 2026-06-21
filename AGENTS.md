# Project Context: Urban Heat Mitigation Hackathon for ISRO

## Team Roles

- **Team Leader (Me):** Module 3 (Physics-Informed ML Engine) & Module 4 (Optimization Logic)
- **Harsh & Shaurya:** Module 1 (Data Pipeline & Geospatial Ingestion)
- **Shubham:** Module 2 (Feature Engineering) & Module 4 UI/UX (Streamlit/Dash)

## Architectural Modules

- **Module 1 (Data):** Landsat 8/ECOSTRESS (LST), Sentinel-2 (LULC), ERA5 (Met data), OpenStreetMap/OSMnx (Morphology). Resampled to 30m grid.
- **Module 2 (Features):** NDVI, NDBI, Albedo, Sky View Factor (SVF). Flattened into a tabular pixel feature matrix.
- **Module 3 (Model):** PyTorch PINN / Hybrid XGBoost mapping drivers to LST with physical constraints.
- **Module 4 (Optimization & UI):** Streamlit frontend allowing scenario simulations (altering Albedo/NDVI) and running optimization algorithms to maximize °C reduction.
