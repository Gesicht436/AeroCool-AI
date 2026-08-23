import React, { useState } from 'react';
import { Play, Zap, Leaf, ShieldCheck } from 'lucide-react';
import { SimulationResult } from '../types';

interface SimulationPanelProps {
  onRunSimulation: (strategy: string, coverage: number, budgetUsd: number) => Promise<SimulationResult | null>;
  currency: 'INR' | 'USD';
  USD_TO_INR: number;
}

export const SimulationPanel: React.FC<SimulationPanelProps> = ({
  onRunSimulation,
  currency,
  USD_TO_INR,
}) => {
  const [strategy, setStrategy] = useState('cool_roof');
  const [coverage, setCoverage] = useState(65);
  const [budgetUsd, setBudgetUsd] = useState(150000);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);

  const handleSimulate = async () => {
    setLoading(true);
    const res = await onRunSimulation(strategy, coverage / 100.0, budgetUsd);
    setResult(res);
    setLoading(false);
  };

  const budgetDisplay =
    currency === 'INR'
      ? `₹${((budgetUsd * USD_TO_INR) / 100000).toFixed(1)} Lakhs`
      : `$${budgetUsd.toLocaleString()} USD`;

  return (
    <div className="glass-panel rounded-2xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Leaf className="w-5 h-5 text-emerald-400" />
            Parametric Cooling Intervention Simulator
          </h2>
          <p className="text-xs text-slate-400">
            Simulate physical thermodynamic cooling shifts tailored to Indian building typologies.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <div className="space-y-4 bg-slate-900/50 p-5 rounded-xl border border-slate-800">
          <div>
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2">
              Intervention Strategy
            </label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-slate-100 text-sm font-semibold rounded-lg p-2.5 focus:ring-2 focus:ring-sky-500"
            >
              <option value="cool_roof">⚪ Cool Roofs (High-Albedo Reflective Coatings)</option>
              <option value="green_roof">🌿 Extensive Green Roofs (Sedum/Crassulacean)</option>
              <option value="urban_canopy">🌳 Urban Tree Canopies (Neem / Peepal / Banyan)</option>
              <option value="cool_pavement">🧱 Permeable & High-Albedo Cool Pavements</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between text-xs font-bold text-slate-300 mb-1">
              <span>Target Coverage:</span>
              <span className="text-sky-400 font-mono">{coverage}%</span>
            </div>
            <input
              type="range"
              min="10"
              max="100"
              step="5"
              value={coverage}
              onChange={(e) => setCoverage(Number(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-400"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-bold text-slate-300 mb-1">
              <span>Capital Budget:</span>
              <span className="text-emerald-400 font-mono">{budgetDisplay}</span>
            </div>
            <input
              type="range"
              min="25000"
              max="500000"
              step="25000"
              value={budgetUsd}
              onChange={(e) => setBudgetUsd(Number(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-400"
            />
          </div>

          <button
            onClick={handleSimulate}
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-bold rounded-xl shadow-lg shadow-sky-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50 cursor-pointer"
          >
            <Play className="w-4 h-4 fill-white" />
            {loading ? 'Simulating Thermodynamics...' : 'Execute Simulation'}
          </button>
        </div>

        {/* Results */}
        <div className="lg:col-span-2 flex flex-col justify-between">
          {result ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="glass-card p-4 rounded-xl">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">Surface LST Drop</div>
                  <div className="text-2xl font-bold font-mono text-sky-400 mt-1">
                    -{result.mean_lst_reduction_celsius.toFixed(2)}°C
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">Peak: -{result.max_lst_reduction_celsius.toFixed(2)}°C</div>
                </div>

                <div className="glass-card p-4 rounded-xl">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">Canopy Air Relief</div>
                  <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                    -{(result.mean_lst_reduction_celsius * 0.35).toFixed(2)}°C
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">2m Pedestrian Ambient</div>
                </div>

                <div className="glass-card p-4 rounded-xl">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">Annual Energy Saved</div>
                  <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
                    {result.annual_cooling_energy_saved_kwh.toLocaleString()}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">kWh / year</div>
                </div>

                <div className="glass-card p-4 rounded-xl">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">CO₂ Mitigated</div>
                  <div className="text-2xl font-bold font-mono text-indigo-300 mt-1">
                    {result.annual_co2_avoided_tons.toFixed(1)}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">Tons / year</div>
                </div>
              </div>

              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <ShieldCheck className="w-6 h-6 text-emerald-400 flex-shrink-0" />
                  <div>
                    <div className="text-sm font-bold text-white">
                      UTCI Thermal Stress Shift: {result.utci_thermal_stress_category_shift}
                    </div>
                    <div className="text-xs text-slate-300">
                      Estimated Financial Payback Period: <span className="text-emerald-300 font-bold">{result.payback_period_years.toFixed(1)} Years</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-400 block">Total Investment</span>
                  <span className="text-sm font-bold font-mono text-white">
                    {currency === 'INR' ? `₹${(result.budget_spent_usd * USD_TO_INR).toLocaleString()}` : `$${result.budget_spent_usd.toLocaleString()} USD`}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-slate-900/30 rounded-xl border border-dashed border-slate-800">
              <Zap className="w-10 h-10 text-slate-600 mb-2" />
              <div className="text-sm font-semibold text-slate-300">No Simulation Executed Yet</div>
              <div className="text-xs text-slate-500 mt-1">
                Configure your strategy and budget on the left to simulate physical cooling.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
