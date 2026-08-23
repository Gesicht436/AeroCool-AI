import React, { useState } from 'react';
import { GitCompare, Zap, CheckCircle2 } from 'lucide-react';
import { SimulationResult } from '../types';

interface ScenarioComparisonProps {
  onRunComparison: (stratA: string, stratB: string, budgetUsd: number) => Promise<{ scenarioA: SimulationResult; scenarioB: SimulationResult }>;
  currency: 'INR' | 'USD';
  USD_TO_INR: number;
}

export const ScenarioComparison: React.FC<ScenarioComparisonProps> = ({
  onRunComparison,
  currency,
  USD_TO_INR,
}) => {
  const [stratA, setStratA] = useState('cool_roof');
  const [stratB, setStratB] = useState('urban_canopy');
  const [budgetUsd, setBudgetUsd] = useState(200000);
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<{ scenarioA: SimulationResult; scenarioB: SimulationResult } | null>(null);

  const handleCompare = async () => {
    setLoading(true);
    try {
      const res = await onRunComparison(stratA, stratB, budgetUsd);
      setComparison(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const budgetLabel =
    currency === 'INR'
      ? `₹${((budgetUsd * USD_TO_INR) / 100000).toFixed(1)} Lakhs`
      : `$${budgetUsd.toLocaleString()} USD`;

  const strategyNames: Record<string, string> = {
    cool_roof: '⚪ Cool Roofs (High Albedo)',
    green_roof: '🌿 Extensive Green Roofs',
    urban_canopy: '🌳 Urban Tree Canopies',
    cool_pavement: '🧱 Permeable Cool Pavements',
  };

  return (
    <div className="glass-panel rounded-2xl p-6 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-indigo-400" />
            Intervention A/B Scenario Comparison
          </h2>
          <p className="text-xs text-slate-400">
            Compare two distinct microclimate cooling policies head-to-head at equal capital investment.
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 bg-slate-900/40 p-4 rounded-xl border border-slate-800">
        <div>
          <label className="text-[11px] font-bold text-sky-400 uppercase tracking-wider block mb-1.5">
            Scenario A (Primary)
          </label>
          <select
            value={stratA}
            onChange={(e) => setStratA(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-100 text-xs font-semibold rounded-lg p-2.5"
          >
            <option value="cool_roof">⚪ Cool Roofs</option>
            <option value="green_roof">🌿 Green Roofs</option>
            <option value="urban_canopy">🌳 Tree Canopies</option>
            <option value="cool_pavement">🧱 Cool Pavements</option>
          </select>
        </div>

        <div>
          <label className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider block mb-1.5">
            Scenario B (Challenger)
          </label>
          <select
            value={stratB}
            onChange={(e) => setStratB(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-slate-100 text-xs font-semibold rounded-lg p-2.5"
          >
            <option value="urban_canopy">🌳 Tree Canopies</option>
            <option value="cool_roof">⚪ Cool Roofs</option>
            <option value="green_roof">🌿 Green Roofs</option>
            <option value="cool_pavement">🧱 Cool Pavements</option>
          </select>
        </div>

        <div>
          <div className="flex justify-between text-[11px] font-bold text-slate-300 mb-1">
            <span>Capital Budget:</span>
            <span className="text-emerald-400 font-mono">{budgetLabel}</span>
          </div>
          <input
            type="range"
            min="50000"
            max="500000"
            step="25000"
            value={budgetUsd}
            onChange={(e) => setBudgetUsd(Number(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-400 mt-2"
          />
        </div>

        <div className="flex flex-col justify-end">
          <button
            onClick={handleCompare}
            disabled={loading}
            className="w-full py-2.5 bg-gradient-to-r from-indigo-500 to-sky-500 hover:from-indigo-400 hover:to-sky-400 text-white text-xs font-bold rounded-lg shadow-md flex items-center justify-center gap-2 cursor-pointer transition-all"
          >
            <Zap className="w-3.5 h-3.5 fill-white" />
            {loading ? 'Evaluating A/B...' : 'Compare Scenarios'}
          </button>
        </div>
      </div>

      {/* Comparison Results Card */}
      {comparison && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Card A */}
          <div className="glass-card p-5 rounded-xl border border-sky-500/30 bg-sky-950/10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-sky-400 uppercase tracking-wider">
                Scenario A: {strategyNames[comparison.scenarioA.strategy_type]}
              </span>
              <CheckCircle2 className="w-4 h-4 text-sky-400" />
            </div>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">Mean Surface Drop:</span>
                <span className="font-mono font-bold text-sky-300">
                  -{comparison.scenarioA.mean_lst_reduction_celsius.toFixed(2)}°C
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">Peak Cooling:</span>
                <span className="font-mono font-bold text-sky-300">
                  -{comparison.scenarioA.max_lst_reduction_celsius.toFixed(2)}°C
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">HVAC Energy Saved:</span>
                <span className="font-mono font-bold text-amber-300">
                  {comparison.scenarioA.annual_cooling_energy_saved_kwh.toLocaleString()} kWh/yr
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">CO₂ Avoided:</span>
                <span className="font-mono font-bold text-emerald-300">
                  {comparison.scenarioA.annual_co2_avoided_tons.toFixed(1)} Tons/yr
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Financial Payback:</span>
                <span className="font-mono font-bold text-white">
                  {comparison.scenarioA.payback_period_years.toFixed(1)} Years
                </span>
              </div>
            </div>
          </div>

          {/* Card B */}
          <div className="glass-card p-5 rounded-xl border border-indigo-500/30 bg-indigo-950/10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                Scenario B: {strategyNames[comparison.scenarioB.strategy_type]}
              </span>
              <CheckCircle2 className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">Mean Surface Drop:</span>
                <span className="font-mono font-bold text-indigo-300">
                  -{comparison.scenarioB.mean_lst_reduction_celsius.toFixed(2)}°C
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">Peak Cooling:</span>
                <span className="font-mono font-bold text-indigo-300">
                  -{comparison.scenarioB.max_lst_reduction_celsius.toFixed(2)}°C
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">HVAC Energy Saved:</span>
                <span className="font-mono font-bold text-amber-300">
                  {comparison.scenarioB.annual_cooling_energy_saved_kwh.toLocaleString()} kWh/yr
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1.5">
                <span className="text-slate-400">CO₂ Avoided:</span>
                <span className="font-mono font-bold text-emerald-300">
                  {comparison.scenarioB.annual_co2_avoided_tons.toFixed(1)} Tons/yr
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Financial Payback:</span>
                <span className="font-mono font-bold text-white">
                  {comparison.scenarioB.payback_period_years.toFixed(1)} Years
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
