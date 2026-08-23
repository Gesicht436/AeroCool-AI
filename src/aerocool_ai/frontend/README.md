# AeroCool-AI Frontend Subsystem (`src/aerocool_ai/frontend/`)

This directory contains the production web client for **AeroCool-AI**, built with **React 19 + TypeScript + Vite + Tailwind CSS + Leaflet**.

---

## Tech Stack & Architecture

| Framework / Tool | Version / Purpose |
|---|---|
| **React 19 + TypeScript** | Strongly typed, reactive component architecture with sub-millisecond re-renders |
| **Vite 6** | Fast HMR dev server and production bundler with Rollup vendor chunk splitting |
| **Tailwind CSS 3** | Glassmorphic dark theme (`#0B0F17`), responsive cards, and print styles |
| **Leaflet & React-Leaflet 5** | High-performance interactive geospatial mapping (Dark Matter, Positron, Esri Satellite) |
| **Recharts** | Interactive SVG Pareto efficiency curves and multi-budget frontier visualization |
| **Lucide Icons** | Clean, accessible vector UI icons |

---

## Directory Layout

```text
src/aerocool_ai/frontend/
├── package.json              # NPM dependencies & scripts
├── vite.config.ts            # Vite bundler, API proxy & Rollup manualChunks config
├── tsconfig.json             # TypeScript compiler configuration
├── tsconfig.node.json        # Vite TypeScript node configuration
├── tailwind.config.js        # Custom Tailwind palette and typography
├── postcss.config.js         # PostCSS plugins
├── index.html                # HTML5 entrypoint with Inter font
├── README.md                 # Documentation (this file)
├── dist/                     # Pre-compiled production React SPA bundle
└── src/                      # React TypeScript source code
    ├── main.tsx              # React DOM root mounting
    ├── App.tsx               # Root application shell, state management & print triggers
    ├── index.css             # Tailwind base styles & glassmorphic utilities
    ├── types/                # TypeScript interfaces (Hotspots, Simulations, Pareto, Presets)
    │   └── index.ts
    ├── services/             # API client service for FastAPI backend
    │   └── api.ts
    └── components/           # Modular React components
        ├── Header.tsx        # Glassmorphic header, status badge, city preset & currency toggle
        ├── MetricCards.tsx   # Top KPI metrics (Baseline LST, Peak Temp, Hotspot Area)
        ├── HotspotMap.tsx    # Leaflet map with dark/satellite tiles, layer switcher & popups
        ├── SimulationPanel.tsx # Parametric cooling intervention sliders & thermodynamic KPIs
        ├── ScenarioComparison.tsx # Head-to-head A/B microclimate policy comparison
        ├── ParetoChart.tsx   # Recharts Pareto investment efficiency frontier
        └── PhysicsPanel.tsx  # Surface Energy Balance & PINN explainers
```

---

## Key Features

1. **Indian City Presets & Regional Profiles**: Instant geospatial bounding boxes and climate zone diagnostics for Delhi NCR, Noida, Mumbai BKC, Nagpur, Bengaluru, and Ahmedabad.
2. **Dual Currency Toggle (₹ INR / $ USD)**: Live conversion (1 USD = ₹83.5 INR) formatted in Lakhs/Crores for municipal budget planners.
3. **Head-to-Head A/B Scenario Comparison**: Evaluate two cooling strategies (e.g. *Cool Roofs* vs *Urban Tree Canopies*) at equivalent capital expenditure with detailed thermodynamic trade-offs.
4. **Printable Municipal Heat Action Plan**: One-click summary export formatted for municipal climate response reports.
5. **Code-Split Optimized Bundle**: Sub-220 kB initial JavaScript payload via Rollup manual chunks (`react-vendor`, `leaflet-vendor`, `recharts-vendor`).

---

## How to Run the Frontend

### Option 1: React 19 Development Server (Port 3000)
```bash
# Navigate to frontend directory
cd src/aerocool_ai/frontend

# Install dependencies (if needed)
npm.cmd install

# Start Vite dev server with Hot Module Reloading (HMR)
npm.cmd run dev
```
- Open in browser: **[http://localhost:3000](http://localhost:3000)**

---

### Option 2: Unified Full-Stack via FastAPI (Port 8000)
The pre-compiled production bundle in `dist/` is mounted automatically inside FastAPI:
```bash
# Start backend server from project root
uv run uvicorn aerocool_ai.backend_api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Open React Dashboard: **[http://localhost:8000/dashboard](http://localhost:8000/dashboard)**
- Open Swagger API Docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**
