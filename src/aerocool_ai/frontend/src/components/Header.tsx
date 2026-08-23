import React from 'react';
import { Sparkles, Globe } from 'lucide-react';
import { CityPreset } from '../types';

interface HeaderProps {
  cities: CityPreset[];
  selectedCity: CityPreset;
  onSelectCity: (city: CityPreset) => void;
  currency: 'INR' | 'USD';
  onToggleCurrency: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  cities,
  selectedCity,
  onSelectCity,
  currency,
  onToggleCurrency,
}) => {
  return (
    <header className="glass-panel rounded-2xl p-6 mb-6 shadow-2xl">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-sky-400 to-indigo-600 p-2.5 rounded-xl shadow-lg shadow-sky-500/20">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl lg:text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-sky-200 to-indigo-200 bg-clip-text text-transparent">
                AeroCool-AI Studio
              </h1>
              <p className="text-xs lg:text-sm text-slate-400 font-medium">
                Physics-Informed Neural Network (PINN) • Geospatial Urban Heat Mitigation
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Status Badge */}
          <div className="inline-flex items-center gap-2 bg-sky-500/10 border border-sky-400/30 text-sky-300 px-3.5 py-1.5 rounded-full text-xs font-semibold">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            SEB Physics Core Online
          </div>

          {/* Currency Toggle */}
          <button
            onClick={onToggleCurrency}
            className="flex items-center gap-1.5 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 px-3 py-1.5 rounded-full text-xs font-bold text-slate-200 transition-all"
            title="Toggle Currency"
          >
            <Globe className="w-3.5 h-3.5 text-sky-400" />
            <span>Currency: {currency === 'INR' ? '₹ INR (Lakhs)' : '$ USD'}</span>
          </button>

          {/* City Selector Dropdown */}
          <div className="relative">
            <select
              value={selectedCity.id}
              onChange={(e) => {
                const found = cities.find((c) => c.id === e.target.value);
                if (found) onSelectCity(found);
              }}
              className="bg-slate-800/90 border border-slate-700 text-slate-100 text-xs lg:text-sm font-semibold rounded-xl px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-sky-500 appearance-none cursor-pointer"
            >
              {cities.map((c) => (
                <option key={c.id} value={c.id}>
                  📍 {c.name}, {c.state} ({c.climateZone})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};
