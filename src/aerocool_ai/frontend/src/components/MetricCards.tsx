import React from 'react';
import { Flame, Thermometer, ShieldAlert, SunDim } from 'lucide-react';

interface MetricCardsProps {
  meanLst: number;
  maxLst: number;
  hotspotCount: number;
  meanAlbedo: number;
}

export const MetricCards: React.FC<MetricCardsProps> = ({
  meanLst,
  maxLst,
  hotspotCount,
  meanAlbedo,
}) => {
  const hotspotHectares = ((hotspotCount * 900) / 10000).toFixed(1);
  const anomalyDelta = (maxLst - meanLst).toFixed(1);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Baseline Mean LST */}
      <div className="glass-card rounded-2xl p-5 relative overflow-hidden transition-all duration-300">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
            Regional Mean LST
          </span>
          <div className="p-2 bg-sky-500/10 rounded-lg text-sky-400">
            <Thermometer className="w-4 h-4" />
          </div>
        </div>
        <div className="text-3xl font-extrabold text-white mt-2 font-mono">
          {meanLst.toFixed(1)}°C
        </div>
        <div className="text-xs text-sky-400 mt-1 font-medium flex items-center gap-1">
          Urban AOI Baseline Average
        </div>
      </div>

      {/* Peak Hotspot */}
      <div className="glass-card rounded-2xl p-5 relative overflow-hidden transition-all duration-300">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
            Peak Surface Temperature
          </span>
          <div className="p-2 bg-rose-500/10 rounded-lg text-rose-400">
            <Flame className="w-4 h-4" />
          </div>
        </div>
        <div className="text-3xl font-extrabold text-rose-400 mt-2 font-mono">
          {maxLst.toFixed(1)}°C
        </div>
        <div className="text-xs text-rose-400/80 mt-1 font-medium">
          +{anomalyDelta}°C Thermal Anomaly
        </div>
      </div>

      {/* Critical Area */}
      <div className="glass-card rounded-2xl p-5 relative overflow-hidden transition-all duration-300">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
            Critical Hotspot Footprint
          </span>
          <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400">
            <ShieldAlert className="w-4 h-4" />
          </div>
        </div>
        <div className="text-3xl font-extrabold text-amber-400 mt-2 font-mono">
          {hotspotHectares} ha
        </div>
        <div className="text-xs text-amber-400/80 mt-1 font-medium">
          {hotspotCount} Priority Urban Parcels
        </div>
      </div>

      {/* Mean Built Albedo */}
      <div className="glass-card rounded-2xl p-5 relative overflow-hidden transition-all duration-300">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
            Built-Up Surface Albedo
          </span>
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
            <SunDim className="w-4 h-4" />
          </div>
        </div>
        <div className="text-3xl font-extrabold text-indigo-300 mt-2 font-mono">
          {meanAlbedo.toFixed(2)}
        </div>
        <div className="text-xs text-indigo-400 mt-1 font-medium">
          High Solar Absorption (Low Reflectance)
        </div>
      </div>
    </div>
  );
};
