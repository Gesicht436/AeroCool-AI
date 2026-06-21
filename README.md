# AeroCool-AI

**Team:** CosmicTensors  
**Project Name:** AeroCool-AI  
**Target Hackathon:** Bharatiya Antariksh Hackathon 2026

AeroCool-AI is a geospatial, physics-informed AI/ML decision-support system designed to identify urban heat stress hotspots, quantify driving factors of land surface temperature (LST), and optimize cooling interventions (such as cool roofs and urban greening) to mitigate urban heat island (UHI) effects.

---

## Problem Statement & Objective

Rapid urbanization leads to the creation of Urban Heat Islands (UHIs), severely affecting energy efficiency, public health, and climate resilience. The objective of **AeroCool-AI** is to build a framework that:

1. **Identifies Urban Heat Hotspots** using remote sensing and meteorological datasets.
2. **Analyzes Drivers of Urban Heating** by quantifying factors like albedo, vegetation indices, sky view factor (SVF), and meteorological variables.
3. **Models Heat Dynamics** through physics-informed machine learning (PINN & Hybrid XGBoost).
4. **Optimizes Cooling Interventions** to simulate changes (e.g., greening, cool roofs) and compute optimal spatial placements for maximizing temperature reduction (°C).

---

## Project Architecture

AeroCool-AI is split into 4 core architectural modules. For a complete deep-dive into our technical architecture, data schema, and algorithms, refer to [ARCHITECTURE.md](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/ARCHITECTURE.md).

```
[Module 1: Data Pipeline] ──> [Module 2: Feature Engineering] ──> [Module 3: Physics-Informed ML]
                                                                        │
[Module 4: Streamlit UI]  <── [Module 4: Optimization Engine]  <────────┘
```

---

## Team Roles & Work Distribution

| Team Member | Module & Scope | Responsibilities |
| :--- | :--- | :--- |
| **Team Leader (Me)** | **Module 3 (Model)** & **Module 4 (Optimization)** | - Build the PyTorch PINN / Hybrid XGBoost models mapping drivers to LST under physical constraints.<br>- Create the optimization algorithms to maximize °C reduction. |
| **Harsh & Shaurya** | **Module 1 (Data & Geospatial Ingestion)** | - Develop data fetchers and downloaders for Landsat 8, ECOSTRESS, Sentinel-2, ERA5, and OSMnx.<br>- Align and resample geospatial layers to a harmonized 30m grid. |
| **Shubham** | **Module 2 (Features)** & **Module 4 (UI/UX)** | - Implement features calculations (NDVI, NDBI, Albedo, Sky View Factor (SVF)).<br>- Construct the tabular pixel feature matrix.<br>- Develop the Streamlit/Dash interactive dashboard for simulations. |

---

## Directory Structure

Below is the directory structure mapped out for the team:

- [data_pipeline/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/data_pipeline) — Module 1: Data ingestion & preprocessing
  - [data_pipeline/ingestion/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/data_pipeline/ingestion) — Multi-source remote sensing downloaders (Landsat, Sentinel, ERA5, OSMnx)
  - [data_pipeline/preprocessing/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/data_pipeline/preprocessing) — Grid resampling (30m) & spatial alignment
- [core_engine/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/core_engine) — Core analytical logic
  - [core_engine/features/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/core_engine/features) — Module 2: NDVI, NDBI, Albedo, and SVF feature engineering
  - [core_engine/models/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/core_engine/models) — Module 3: Physics-Informed Neural Networks & Hybrid ML Engines
  - [core_engine/optimization/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/core_engine/optimization) — Module 4: Cooling intervention optimizations
  - [core_engine/dashboard/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/core_engine/dashboard) — Module 4: Streamlit-based interactive UI
- [quality_assurance/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/quality_assurance) — Testing suites
  - [quality_assurance/tests/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/quality_assurance/tests) — Unit and integration tests
  - [quality_assurance/validation/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/quality_assurance/validation) — Physical constraints validator
- [project_assets/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/project_assets) — Media, maps, layouts, and documentation assets
- [misc_scripts/](file:///C:/Users/mayan/Coding/Hackathons/Cosmic-Tensors/misc_scripts) — Notebooks and helper utilities

---

## Quickstart Setup

This project uses [uv](https://github.com/astral-sh/uv) for lightning-fast environment and package management. Ensure you have Python 3.14+ and `uv` installed.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Gesicht436/AeroCool-AI.git
   cd Cosmic-Tensors
   ```

2. **Set up the virtual environment and install dependencies:**

   ```bash
   # Create a virtual environment and install dependencies in editable mode
   uv sync
   ```

3. **Run the Streamlit Dashboard:**

   ```bash
   uv run streamlit run core_engine/dashboard/app.py
   ```
