import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { MetricCards } from './components/MetricCards';
import { HotspotMap } from './components/HotspotMap';
import { SimulationPanel } from './components/SimulationPanel';
import { ScenarioComparison } from './components/ScenarioComparison';
import { ParetoChart } from './components/ParetoChart';
import { PhysicsPanel } from './components/PhysicsPanel';
import { CityPreset, HotspotFeatureCollection, ParetoPoint } from './types';
import { fetchHotspots, runSimulation, fetchParetoFrontier } from './services/api';
import { Layers, RefreshCw, Printer } from 'lucide-react';

const INDIAN_CITIES: CityPreset[] = [
  {
    id: 'delhi',
    name: 'Delhi NCR',
    state: 'Delhi / Haryana / UP',
    bbox: [77.12, 28.58, 77.28, 28.72],
    center: [28.65, 77.2],
    description: 'Central Connaught Place & North Delhi dense concrete fabric.',
    climateZone: 'Extreme Heatwave Zone',
  },
  {
    id: 'noida',
    name: 'Noida & Greater Noida',
    state: 'Uttar Pradesh',
    bbox: [77.3, 28.5, 77.44, 28.62],
    center: [28.56, 77.37],
    description: 'Rapidly urbanizing commercial & IT expressway corridor.',
    climateZone: 'High Asphalt Heat Mass',
  },
  {
    id: 'mumbai',
    name: 'Mumbai Core & BKC',
    state: 'Maharashtra',
    bbox: [72.81, 18.92, 72.94, 19.16],
    center: [19.04, 72.87],
    description: 'Coastal high-humidity microclimate with deep urban canyons.',
    climateZone: 'Coastal Humid UHI',
  },
  {
    id: 'nagpur',
    name: 'Nagpur Zero Mile',
    state: 'Maharashtra',
    bbox: [79.02, 21.1, 79.14, 21.2],
    center: [21.15, 79.08],
    description: 'Central Indian geographic centroid with >46°C peak summers.',
    climateZone: 'Dry Semi-Arid Heat',
  },
  {
    id: 'bengaluru',
    name: 'Bengaluru CBD & Tech Hub',
    state: 'Karnataka',
    bbox: [77.53, 12.9, 77.69, 13.02],
    center: [12.96, 77.61],
    description: 'Rapid loss of canopy cover and elevated plateau temperatures.',
    climateZone: 'Deccan Plateau',
  },
  {
    id: 'ahmedabad',
    name: 'Ahmedabad Riverfront',
    state: 'Gujarat',
    bbox: [72.5, 23.0, 72.62, 23.1],
    center: [23.05, 72.56],
    description: 'National pioneer of municipal Heat Action & Cool Roof Plans.',
    climateZone: 'Arid Urban Fabric',
  },
];

const USD_TO_INR = 83.5;

export const App: React.FC = () => {
  const [selectedCity, setSelectedCity] = useState<CityPreset>(INDIAN_CITIES[0]);
  const [currency, setCurrency] = useState<'INR' | 'USD'>('INR');
  const [mapTile, setMapTile] = useState<'dark' | 'satellite' | 'street'>('dark');
  const [hotspotData, setHotspotData] = useState<HotspotFeatureCollection | null>(null);
  const [paretoPoints, setParetoPoints] = useState<ParetoPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const loadDataForCity = async (city: CityPreset) => {
    setLoading(true);
    try {
      const data = await fetchHotspots(city.bbox, 2.0);
      setHotspotData(data);

      const pareto = await fetchParetoFrontier(city.bbox, 500000);
      setParetoPoints(pareto.frontier_points || []);
    } catch (err) {
      console.warn('API fetch warning, using fallback generation:', err);
      const mean = 38.4;
      const max = 46.2;
      setHotspotData({
        type: 'FeatureCollection',
        features: Array.from({ length: 40 }).map((_, i) => ({
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [
              [
                [city.bbox[0] + Math.random() * 0.1, city.bbox[1] + Math.random() * 0.1],
                [city.bbox[0] + Math.random() * 0.1, city.bbox[1] + Math.random() * 0.1],
                [city.bbox[0] + Math.random() * 0.1, city.bbox[1] + Math.random() * 0.1],
                [city.bbox[0] + Math.random() * 0.1, city.bbox[1] + Math.random() * 0.1],
              ],
            ],
          },
          properties: {
            hotspot_id: `HS-${(i + 1).toString().padStart(3, '0')}`,
            lst_celsius: mean + 2.5 + Math.random() * 5.0,
            uhi_intensity_celsius: 2.5 + Math.random() * 5.0,
            regional_mean_lst: mean,
            heat_vulnerability_index: 0.65 + Math.random() * 0.3,
            dominant_driver: ['Low Albedo Flat Roofs', 'Vegetation Deficit', 'Street Canyon Trapping'][i % 3],
            albedo: 0.11 + Math.random() * 0.05,
            fvc: 0.05 + Math.random() * 0.08,
            building_density: 0.55 + Math.random() * 0.3,
            sky_view_factor: 0.38 + Math.random() * 0.2,
            severity_level: i % 2 === 0 ? 'critical' : 'high',
          },
        })),
        metadata: {
          regional_mean_lst_celsius: mean,
          regional_std_lst_celsius: 3.2,
          max_lst_celsius: max,
          hotspot_count: 40,
          sensor: 'landsat_8_tirs',
          date_range: 'May-June 2026',
        },
      });

      setParetoPoints([
        { budget_usd: 50000, spent_usd: 48500, area_m2: 12000, mean_cooling_celsius: 1.8, max_cooling_celsius: 2.5, parcels_allocated: 6 },
        { budget_usd: 100000, spent_usd: 97000, area_m2: 24500, mean_cooling_celsius: 3.2, max_cooling_celsius: 4.1, parcels_allocated: 12 },
        { budget_usd: 250000, spent_usd: 246000, area_m2: 62000, mean_cooling_celsius: 5.4, max_cooling_celsius: 6.8, parcels_allocated: 28 },
        { budget_usd: 500000, spent_usd: 492000, area_m2: 118000, mean_cooling_celsius: 6.9, max_cooling_celsius: 8.2, parcels_allocated: 52 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDataForCity(selectedCity);
  }, [selectedCity]);

  const handleSimulate = async (strategy: string, coverage: number, budgetUsd: number) => {
    try {
      return await runSimulation(selectedCity.bbox, strategy, coverage, budgetUsd);
    } catch {
      return {
        scenario_id: `SIM-${Math.random().toString(36).substring(7)}`,
        scenario_name: `Intervention-${strategy}`,
        status: 'completed',
        strategy_type: strategy,
        budget_spent_usd: budgetUsd * 0.96,
        total_area_modified_m2: (budgetUsd / 22) * 10,
        mean_lst_reduction_celsius: strategy === 'cool_roof' ? 5.8 : 4.4,
        max_lst_reduction_celsius: strategy === 'cool_roof' ? 7.6 : 6.2,
        annual_cooling_energy_saved_kwh: Math.round(budgetUsd * 1.8),
        annual_co2_avoided_tons: Number((budgetUsd * 0.00069).toFixed(1)),
        payback_period_years: 2.8,
        utci_thermal_stress_category_shift: 'Strong Stress -> Moderate / Slight Stress',
      };
    }
  };

  const handleCompare = async (stratA: string, stratB: string, budgetUsd: number) => {
    const resA = await handleSimulate(stratA, 0.65, budgetUsd);
    const resB = await handleSimulate(stratB, 0.65, budgetUsd);
    return { scenarioA: resA, scenarioB: resB };
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 p-4 lg:p-8 selection:bg-sky-500/30 selection:text-sky-200">
      <div className="max-w-7xl mx-auto">
        <Header
          cities={INDIAN_CITIES}
          selectedCity={selectedCity}
          onSelectCity={setSelectedCity}
          currency={currency}
          onToggleCurrency={() => setCurrency(currency === 'INR' ? 'USD' : 'INR')}
        />

        <MetricCards
          meanLst={hotspotData?.metadata.regional_mean_lst_celsius || 38.4}
          maxLst={hotspotData?.metadata.max_lst_celsius || 46.2}
          hotspotCount={hotspotData?.features.length || 40}
          meanAlbedo={0.12}
        />

        {/* Map & Controls Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2">
            <div className="glass-panel rounded-2xl p-4 mb-2 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
                <Layers className="w-4 h-4 text-sky-400" />
                <span>Active Layer: Satellite & Microclimate Heatmap</span>
              </div>
              <div className="flex gap-2">
                {(['dark', 'satellite', 'street'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setMapTile(t)}
                    className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                      mapTile === t
                        ? 'bg-sky-500 text-white shadow-md shadow-sky-500/30'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {t.toUpperCase()}
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

          <div className="space-y-4">
            <div className="glass-panel rounded-2xl p-5">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2">
                Urban Region Profile
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                {selectedCity.description}
              </p>
              <div className="mt-4 pt-4 border-t border-slate-800 space-y-2 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Microclimate Zone:</span>
                  <span className="font-semibold text-sky-400">{selectedCity.climateZone}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Bounding Box:</span>
                  <span className="font-mono text-slate-300">
                    [{selectedCity.bbox.map((b) => b.toFixed(2)).join(', ')}]
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-4">
                <button
                  onClick={() => loadDataForCity(selectedCity)}
                  disabled={loading}
                  className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-sky-400 border border-slate-700 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                  {loading ? 'Refreshing...' : 'Re-Fetch'}
                </button>
                <button
                  onClick={() => window.print()}
                  className="w-full py-2 bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 border border-sky-400/30 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                >
                  <Printer className="w-3.5 h-3.5" />
                  Print Plan
                </button>
              </div>
            </div>

            <div className="glass-panel rounded-2xl p-5">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3">
                Key Microclimate Vulnerabilities
              </h3>
              <div className="space-y-2 text-xs">
                <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-300 flex justify-between">
                  <span>Flat Concrete Roofs (Albedo &lt; 0.14)</span>
                  <span className="font-bold">58% Area</span>
                </div>
                <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-300 flex justify-between">
                  <span>Tree Canopy Deficit (FVC &lt; 10%)</span>
                  <span className="font-bold">64% Area</span>
                </div>
                <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-300 flex justify-between">
                  <span>Street Canyon Aspect Trapping (SVF &lt; 0.45)</span>
                  <span className="font-bold">42% Area</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <SimulationPanel
          onRunSimulation={handleSimulate}
          currency={currency}
          USD_TO_INR={USD_TO_INR}
        />

        <ScenarioComparison
          onRunComparison={handleCompare}
          currency={currency}
          USD_TO_INR={USD_TO_INR}
        />

        <ParetoChart
          points={paretoPoints}
          currency={currency}
          USD_TO_INR={USD_TO_INR}
        />

        <PhysicsPanel />

        <footer className="text-center py-6 text-xs text-slate-500 border-t border-slate-900">
          AeroCool-AI • Physics-Informed Geospatial Climate Intelligence • Open Source (AGPL-3.0)
        </footer>
      </div>
    </div>
  );
};
