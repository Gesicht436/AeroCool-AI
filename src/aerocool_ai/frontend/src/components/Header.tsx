import React from 'react';
import { Sparkles, Globe, Shield, LogIn, LogOut, ArrowLeftRight, LayoutDashboard } from 'lucide-react';
import { CityPreset } from '../types';
import { useAuth } from '../context/AuthContext';

interface HeaderProps {
  cities: CityPreset[];
  selectedCity: CityPreset;
  onSelectCity: (city: CityPreset) => void;
  currency: 'INR' | 'USD';
  onToggleCurrency: () => void;
  currentView: 'studio' | 'admin';
  onToggleView: (view: 'studio' | 'admin') => void;
}

export const Header: React.FC<HeaderProps> = ({
  cities,
  selectedCity,
  onSelectCity,
  currency,
  onToggleCurrency,
  currentView,
  onToggleView,
}) => {
  const { user, isAdmin, openLoginModal, quickSwitchRole, logout } = useAuth();

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
          {/* Admin / Studio View Switcher (Only visible to Admin) */}
          {isAdmin && (
            <div className="flex bg-slate-900 border border-purple-500/30 p-1 rounded-xl">
              <button
                onClick={() => onToggleView('studio')}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
                  currentView === 'studio'
                    ? 'bg-sky-500 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <LayoutDashboard className="w-3.5 h-3.5" />
                Cooling Studio
              </button>
              <button
                onClick={() => onToggleView('admin')}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
                  currentView === 'admin'
                    ? 'bg-purple-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Shield className="w-3.5 h-3.5" />
                Admin Telemetry
              </button>
            </div>
          )}

          {/* User Account & Role Badge */}
          <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-xl">
            <div
              className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
                isAdmin
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                  : 'bg-sky-500/20 text-sky-300 border border-sky-500/40'
              }`}
            >
              {isAdmin ? '👑' : '🏛️'}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
                <span>{user?.full_name || 'Guest User'}</span>
                <span
                  className={`text-[9px] font-extrabold uppercase px-1.5 py-0.2 rounded ${
                    isAdmin ? 'bg-purple-500/20 text-purple-300' : 'bg-sky-500/20 text-sky-300'
                  }`}
                >
                  {isAdmin ? 'Admin' : 'Planner'}
                </span>
              </div>
              <div className="text-[10px] text-slate-400 truncate max-w-[140px]">
                {user?.organization || user?.email}
              </div>
            </div>

            {/* Quick 1-Click Role Switcher */}
            <button
              onClick={() => quickSwitchRole(isAdmin ? 'customer' : 'admin')}
              className="ml-1 p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors cursor-pointer"
              title={`Switch to ${isAdmin ? 'Customer/Planner' : 'Admin'} Role`}
            >
              <ArrowLeftRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Currency Toggle */}
          <button
            onClick={onToggleCurrency}
            className="flex items-center gap-1.5 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-200 transition-all cursor-pointer"
            title="Toggle Currency"
          >
            <Globe className="w-3.5 h-3.5 text-sky-400" />
            <span>{currency === 'INR' ? '₹ INR' : '$ USD'}</span>
          </button>

          {/* City Selector Dropdown (When in studio view) */}
          {currentView === 'studio' && (
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
                    📍 {c.name} ({c.climateZone})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Sign In & Log Out Actions */}
          <button
            onClick={openLoginModal}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 rounded-xl transition-all cursor-pointer"
            title="Account Access & Sign In"
          >
            <LogIn className="w-4 h-4" />
          </button>

          <button
            onClick={logout}
            className="p-2 bg-slate-800 hover:bg-rose-950/40 hover:border-rose-500/40 text-slate-400 hover:text-rose-300 border border-slate-700 rounded-xl transition-all cursor-pointer"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
