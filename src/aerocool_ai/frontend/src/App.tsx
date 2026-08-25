import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { MetricCards } from './components/MetricCards';
import { HotspotMap } from './components/HotspotMap';
import { PhysicsPanel } from './components/PhysicsPanel';
import { SimulationPanel } from './components/SimulationPanel';
import { ScenarioComparison } from './components/ScenarioComparison';
import { ParetoChart } from './components/ParetoChart';
import { AdminDashboard } from './components/AdminDashboard';
import { LoginModal } from './components/LoginModal';
import { useAuth } from './context/AuthContext';
import { CityPreset, HotspotFeatureCollection, ParetoPoint, SimulationResult } from './types';
import { fetchHotspots, fetchParetoFrontier, runSimulation } from './services/api';
import { AlertTriangle, RefreshCw } from 'lucide-react';

const USD_TO_INR = 83.5;

const INDIAN_CITIES: CityPreset[] = [
  {
    id: 'delhi',
    name: 'Delhi NCR',
    state: 'National Capital Territory',
    bbox: [77.10, 28.58, 77.26, 28.72],
    center: [28.65, 77.18],
    description: 'High-density urban fabric with severe summer heat island and low rooftop albedo.',
    climateZone: 'Semi-Arid / Composite',
  },
  {
    id: 'mumbai',
    name: 'Mumbai',
    state: 'Maharashtra',
    bbox: [72.82, 19.00, 72.95, 19.15],
    center: [19.07, 72.88],
    description: 'Coastal megacity with extreme humidity and nocturnal heat entrapment.',
    climateZone: 'Tropical Wet & Dry',
  },
  {
    id: 'ahmedabad',
    name: 'Ahmedabad',
    state: 'Gujarat',
    bbox: [72.50, 22.95, 72.65, 23.08],
    center: [23.02, 72.57],
    description: 'Pioneer Heat Action Plan city with extensive cool roof implementation.',
    climateZone: 'Hot Semi-Arid',
  },
  {
    id: 'chennai',
    name: 'Chennai',
    state: 'Tamil Nadu',
    bbox: [80.18, 12.98, 80.30, 13.12],
    center: [13.05, 80.24],
    description: 'High solar irradiance with dense commercial corridors.',
    climateZone: 'Tropical Wet & Dry',
  },
  {
    id: 'bengaluru',
    name: 'Bengaluru',
    state: 'Karnataka',
    bbox: [77.52, 12.90, 77.68, 13.02],
    center: [12.96, 77.60],
    description: 'Rapidly expanding tech corridor with vegetation canopy loss.',
    climateZone: 'Tropical Savanna',
  },
  {
    id: 'hyderabad',
    name: 'Hyderabad',
    state: 'Telangana',
    bbox: [78.40, 17.34, 78.54, 17.46],
    center: [17.40, 78.47],
    description: 'Deccan plateau urban core with high asphalt and concrete heat retention.',
    climateZone: 'Tropical Wet & Dry',
  },
];

export const App: React.FC = () => {
  const { isAdmin } = useAuth();
  const [currentView, setCurrentView] = useState<'studio' | 'admin'>('studio');
  const [selectedCity, setSelectedCity] = useState<CityPreset>(INDIAN_CITIES[0]);
  const [hotspotData, setHotspotData] = useState<HotspotFeatureCollection | null>(null);
  const [paretoPoints, setParetoPoints] = useState<ParetoPoint[]>([]);
  const [mapTile, setMapTile] = useState<'dark' | 'satellite' | 'street'>('dark');
  const [currency, setCurrency] = useState<'INR' | 'USD'>('INR');
  const [loading, setLoading] = useState<boolean>(true);
  const [apiError, setApiError] = useState<string | null>(null);

  // Switch view if admin logs out
  useEffect(() => {
    if (!isAdmin && currentView === 'admin') {
      setCurrentView('studio');
    }
  }, [isAdmin, currentView]);

  const loadDataForCity = async (city: CityPreset) => {
    setLoading(true);
    setApiError(null);
    try {
      const data = await fetchHotspots(city.bbox, 2.0);
      setHotspotData(data);

      const pareto = await fetchParetoFrontier(city.bbox, 500000);
      setParetoPoints(pareto.frontier_points || []);
    } catch (err: any) {
      console.error('API fetch failed in strict mode:', err);
      setApiError(err?.message || 'Failed to fetch urban heat island hotspots from backend API.');
      setHotspotData(null);
      setParetoPoints([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDataForCity(selectedCity);
  }, [selectedCity]);

  const handleRunSimulation = async (
    strategy: string,
    coverage: number,
    budgetUsd: number
  ): Promise<SimulationResult | null> => {
    return await runSimulation(selectedCity.bbox, strategy, coverage, budgetUsd);
  };

  const handleRunComparison = async (
    stratA: string,
    stratB: string,
    budgetUsd: number
  ): Promise<{ scenarioA: SimulationResult; scenarioB: SimulationResult }> => {
    const scenarioA = await runSimulation(selectedCity.bbox, stratA, 0.65, budgetUsd);
    const scenarioB = await runSimulation(selectedCity.bbox, stratB, 0.65, budgetUsd);
    return { scenarioA, scenarioB };
  };

  const meanLst = hotspotData?.metadata?.regional_mean_lst_celsius ?? 35.0;
  const maxLst = hotspotData?.metadata?.max_lst_celsius ?? 44.0;
  const hotspotCount = hotspotData?.features?.length ?? 0;
  const meanAlbedo = 0.14;

  return (
    <div className="min-h-screen bg-[#070B14] text-slate-100 p-4 lg:p-8 selection:bg-sky-500/30 selection:text-sky-200">
      <div className="max-w-7xl mx-auto">
        <Header
          cities={INDIAN_CITIES}
          selectedCity={selectedCity}
          onSelectCity={setSelectedCity}
          currency={currency}
          onToggleCurrency={() => setCurrency(currency === 'INR' ? 'USD' : 'INR')}
          currentView={currentView}
          onToggleView={setCurrentView}
        />

        {apiError && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between text-rose-200 shadow-lg">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
              <div>
                <div className="font-semibold text-rose-300">Strict Error Mode — Backend API Failure</div>
                <div className="text-xs text-rose-200/80 font-mono mt-0.5">{apiError}</div>
              </div>
            </div>
            <button
              onClick={() => loadDataForCity(selectedCity)}
              className="px-3.5 py-2 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-xs font-semibold transition flex items-center gap-1.5 shrink-0"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry API
            </button>
          </div>
        )}

        {currentView === 'admin' && isAdmin ? (
          <AdminDashboard />
        ) : (
          <main className="space-y-6">
            {/* Top Metric Cards */}
            <MetricCards
              meanLst={meanLst}
              maxLst={maxLst}
              hotspotCount={hotspotCount}
              meanAlbedo={meanAlbedo}
            />

            {/* Main Interactive Map */}
            <div className="glass-panel rounded-2xl p-6 mb-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    Spatial Urban Heat Island (UHI) Thermal Hotspot Map
                  </h2>
                  <p className="text-xs text-slate-400">
                    High-resolution thermal infrared satellite observations with building plan density and albedo driver overlays.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-medium">Basemap:</span>
                  {(['dark', 'satellite', 'street'] as const).map((tile) => (
                    <button
                      key={tile}
                      onClick={() => setMapTile(tile)}
                      className={`px-2.5 py-1 text-xs font-semibold rounded-lg capitalize transition ${
                        mapTile === tile
                          ? 'bg-sky-500 text-white shadow-md shadow-sky-500/30'
                          : 'bg-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      {tile}
                    </button>
                  ))}
                </div>
              </div>

              <HotspotMap
                bbox={selectedCity.bbox}
                center={selectedCity.center}
                hotspots={hotspotData?.features || []}
                mapTile={mapTile}
              />
            </div>

            {/* Simulation Engine Panel */}
            <SimulationPanel
              onRunSimulation={handleRunSimulation}
              currency={currency}
              USD_TO_INR={USD_TO_INR}
            />

            {/* A/B Policy Scenario Comparison */}
            <ScenarioComparison
              onRunComparison={handleRunComparison}
              currency={currency}
              USD_TO_INR={USD_TO_INR}
            />

            {/* Pareto Multi-Objective Frontier Chart */}
            <ParetoChart
              points={paretoPoints}
              currency={currency}
              USD_TO_INR={USD_TO_INR}
            />

            {/* Physics Formulation Documentation */}
            <PhysicsPanel />
          </main>
        )}

        {loading && (
          <div className="mb-4 text-xs text-sky-400 font-mono flex items-center gap-2">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            Loading urban thermal observations and Pareto optimization curve...
          </div>
        )}

        <footer className="mt-12 text-center text-xs text-slate-500 border-t border-slate-800/60 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            <span>AeroCool-AI Engine v0.1.0 (Strict Error Mode Active)</span>
          </div>
          <div>Physics-Informed Neural Network (PINN) + PostGIS Geospatial Persistence</div>
        </footer>
      </div>

      <LoginModal />
    </div>
  );
};

export default App;
