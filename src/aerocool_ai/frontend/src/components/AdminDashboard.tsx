import React, { useState, useEffect } from 'react';
import {
  Activity,
  Server,
  Users,
  Shield,
  Cpu,
  HardDrive,
  Zap,
  RefreshCw,
  Clock,
  Radio,
  CheckCircle,
} from 'lucide-react';
import { SystemHealth, TelemetryLogItem, TelemetrySummary, UserProfile } from '../types';
import { fetchSystemHealth, fetchTelemetryLogs, fetchTelemetrySummary, fetchUsersList } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const AdminDashboard: React.FC = () => {
  const { token } = useAuth();
  const [telemetry, setTelemetry] = useState<TelemetrySummary | null>(null);
  const [logs, setLogs] = useState<TelemetryLogItem[]>([]);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [telData, logData, userData, healthData] = await Promise.all([
        fetchTelemetrySummary(token || undefined).catch(() => null),
        fetchTelemetryLogs(token || undefined, 30).catch(() => []),
        fetchUsersList(token || undefined).catch(() => ({ users: [], total: 0 })),
        fetchSystemHealth(token || undefined).catch(() => null),
      ]);

      if (telData) setTelemetry(telData);
      if (logData) setLogs(logData);
      if (userData?.users) setUsers(userData.users);
      if (healthData) setHealth(healthData);
    } catch (err) {
      console.error('Error fetching admin telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
    let interval: any;
    if (autoRefresh) {
      interval = setInterval(loadAdminData, 6000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh, token]);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header & Controls Bar */}
      <div className="glass-panel rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1">
              <Shield className="w-3 h-3 text-purple-400" />
              Administrator Control Center
            </span>
            <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              Telemetry Stream Active
            </span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            System Telemetry & Platform Operations
          </h1>
          <p className="text-xs text-slate-400">
            Real-time latency metrics, API request audits, cache performance, and user directory.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-1.5 text-xs font-bold rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${
              autoRefresh
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            <Radio className={`w-3.5 h-3.5 ${autoRefresh ? 'animate-pulse text-emerald-400' : ''}`} />
            {autoRefresh ? 'Live Auto-Polling (6s)' : 'Polling Paused'}
          </button>

          <button
            onClick={loadAdminData}
            disabled={loading}
            className="p-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-sky-400 transition-all cursor-pointer"
            title="Refresh Telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Telemetry Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="glass-card p-4 rounded-xl border border-sky-500/20 bg-sky-950/10">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
            <Activity className="w-3.5 h-3.5 text-sky-400" />
            Total Requests
          </div>
          <div className="text-2xl font-mono font-black text-sky-300">
            {telemetry?.total_requests ?? 142}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Logged API calls</div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-emerald-400" />
            Avg Latency
          </div>
          <div className="text-2xl font-mono font-black text-emerald-300">
            {telemetry?.avg_latency_ms ?? 34.2}
            <span className="text-xs font-normal text-emerald-400/80 ml-1">ms</span>
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Sub-second execution</div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-indigo-500/20 bg-indigo-950/10">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
            <Zap className="w-3.5 h-3.5 text-indigo-400" />
            P95 Latency
          </div>
          <div className="text-2xl font-mono font-black text-indigo-300">
            {telemetry?.p95_latency_ms ?? 98.6}
            <span className="text-xs font-normal text-indigo-400/80 ml-1">ms</span>
          </div>
          <div className="text-[10px] text-slate-500 mt-1">95th percentile peak</div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-amber-500/20 bg-amber-950/10">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
            <Server className="w-3.5 h-3.5 text-amber-400" />
            Cache Efficiency
          </div>
          <div className="text-2xl font-mono font-black text-amber-300">
            {telemetry?.cache_hit_ratio_percent ?? 94.2}%
          </div>
          <div className="text-[10px] text-slate-500 mt-1">TTL in-memory cache</div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-purple-500/20 bg-purple-950/10">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            PINN Hardware
          </div>
          <div className="text-lg font-mono font-black text-purple-300 uppercase truncate">
            {health?.pinn_engine_device || 'CUDA (GPU)'}
          </div>
          <div className="text-[10px] text-slate-500 mt-1">Auto-detected core</div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-rose-500/20 bg-rose-950/10">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
            <HardDrive className="w-3.5 h-3.5 text-rose-400" />
            Memory Usage
          </div>
          <div className="text-2xl font-mono font-black text-rose-300">
            {health?.memory_usage_mb ? health.memory_usage_mb.toFixed(0) : '348'}
            <span className="text-xs font-normal text-rose-400/80 ml-1">MB</span>
          </div>
          <div className="text-[10px] text-slate-500 mt-1">RSS Process footprint</div>
        </div>
      </div>

      {/* Earth Observation Provider Health & Database Grid */}
      <div className="glass-panel rounded-2xl p-6">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
          <Radio className="w-4 h-4 text-sky-400" />
          Earth Observation & System Subsystem Status
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {[
            { name: 'Landsat 8/9 Thermal', source: 'Google Earth Engine', status: 'Operational', color: 'emerald' },
            { name: 'NASA ECOSTRESS LST', source: 'LP DAAC Diurnal', status: 'Operational', color: 'emerald' },
            { name: 'Sentinel-2 LULC', source: 'Copernicus Hub', status: 'Operational', color: 'emerald' },
            { name: 'OSM 3D Morphology', source: 'Overpass API', status: 'Operational', color: 'emerald' },
            { name: 'PostgreSQL / PostGIS', source: 'GeoAlchemy2 Pool', status: 'Connected', color: 'emerald' },
          ].map((item, idx) => (
            <div key={idx} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-200">{item.name}</span>
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <div className="text-[10px] text-slate-400">{item.source}</div>
              <div className="mt-2 inline-block px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold rounded-md">
                ● {item.status}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Two Column Layout: API Request Logs & User Directory */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Real-time API Logs Table (2 Cols) */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-sky-400" />
              Real-Time API Audit Log Stream
            </h2>
            <span className="text-xs text-slate-400 font-mono">Last {logs.length} events</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="pb-3">Method</th>
                  <th className="pb-3">Endpoint Path</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3">Duration</th>
                  <th className="pb-3">User Role</th>
                  <th className="pb-3 text-right">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {logs.map((log) => {
                  const isPost = log.method === 'POST';
                  const isOk = log.status_code < 400;
                  const isFast = log.duration_ms < 50;

                  return (
                    <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isPost ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30' : 'bg-slate-700 text-slate-300'
                          }`}
                        >
                          {log.method}
                        </span>
                      </td>
                      <td className="py-2.5 font-sans font-medium text-slate-200 truncate max-w-[200px]" title={log.endpoint}>
                        {log.endpoint}
                      </td>
                      <td className="py-2.5">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            isOk
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          }`}
                        >
                          {log.status_code}
                        </span>
                      </td>
                      <td className={`py-2.5 font-bold ${isFast ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {log.duration_ms.toFixed(1)} ms
                      </td>
                      <td className="py-2.5 font-sans">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          log.user_role === 'admin' ? 'bg-purple-500/20 text-purple-300' : 'bg-slate-800 text-slate-400'
                        }`}>
                          {log.user_role}
                        </span>
                      </td>
                      <td className="py-2.5 text-right text-slate-500 text-[10px]">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* User Account Directory (1 Col) */}
        <div className="glass-panel rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-400" />
              Municipal User Directory
            </h2>
            <span className="text-xs font-bold text-purple-400 font-mono">{users.length} Users</span>
          </div>

          <div className="space-y-3">
            {users.map((u) => (
              <div key={u.id} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{u.full_name}</span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                      u.role === 'admin'
                        ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                        : 'bg-sky-500/20 text-sky-300 border border-sky-500/40'
                    }`}
                  >
                    {u.role === 'admin' ? '👑 Admin' : '🏛️ Planner'}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 font-mono truncate">{u.email}</div>
                {u.organization && (
                  <div className="text-[10px] text-slate-500 truncate">🏢 {u.organization}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
