import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, UserCheck, Lock, Mail, User, Building, X, AlertCircle } from 'lucide-react';
import { UserRole } from '../types';

export const LoginModal: React.FC = () => {
  const { isLoginModalOpen, closeLoginModal, login, register, quickSwitchRole } = useAuth();

  const [tab, setTab] = useState<'signin' | 'register'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [organization, setOrganization] = useState('');
  const [role, setRole] = useState<UserRole>('customer');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isLoginModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (tab === 'signin') {
        await login(email, password);
      } else {
        await register(email, password, fullName, role, organization);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = async (demoRole: 'admin' | 'customer') => {
    setLoading(true);
    setError(null);
    try {
      await quickSwitchRole(demoRole);
      closeLoginModal();
    } catch (err: any) {
      setError(err.message || 'Demo switch failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-[#0F172A] border border-slate-700/60 rounded-2xl shadow-2xl p-6 overflow-hidden">
        {/* Glow Header Accent */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-sky-500 via-indigo-500 to-purple-500" />

        {/* Close Button */}
        <button
          onClick={closeLoginModal}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Title */}
        <div className="mb-6 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400 mb-3">
            <Lock className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            AeroCool-AI Portal Access
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Sign in to access geospatial physics models and municipal telemetry.
          </p>
        </div>

        {/* 1-Click Demo Quick Switch Cards */}
        <div className="mb-5 bg-slate-900/60 border border-slate-800 rounded-xl p-3">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2 text-center">
            ⚡ Instant 1-Click Demo Profiles
          </span>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickDemo('admin')}
              disabled={loading}
              className="flex items-center gap-2 p-2.5 bg-purple-950/40 hover:bg-purple-900/40 border border-purple-500/30 hover:border-purple-400/60 rounded-xl transition-all text-left cursor-pointer group"
            >
              <ShieldCheck className="w-5 h-5 text-purple-400 group-hover:scale-110 transition-transform flex-shrink-0" />
              <div>
                <div className="text-xs font-bold text-purple-300">Admin User</div>
                <div className="text-[10px] text-purple-400/80">Full Telemetry & Mgmt</div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickDemo('customer')}
              disabled={loading}
              className="flex items-center gap-2 p-2.5 bg-sky-950/40 hover:bg-sky-900/40 border border-sky-500/30 hover:border-sky-400/60 rounded-xl transition-all text-left cursor-pointer group"
            >
              <UserCheck className="w-5 h-5 text-sky-400 group-hover:scale-110 transition-transform flex-shrink-0" />
              <div>
                <div className="text-xs font-bold text-sky-300">Customer User</div>
                <div className="text-[10px] text-sky-400/80">Planners & Action Plans</div>
              </div>
            </button>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-800 mb-4">
          <button
            type="button"
            onClick={() => { setTab('signin'); setError(null); }}
            className={`flex-1 py-2 text-xs font-bold border-b-2 transition-all ${
              tab === 'signin'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setTab('register'); setError(null); }}
            className={`flex-1 py-2 text-xs font-bold border-b-2 transition-all ${
              tab === 'register'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          {tab === 'register' && (
            <>
              <div>
                <label className="text-[11px] font-bold text-slate-400 block mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    required
                    placeholder="e.g. Dr. Priya Sharma"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full bg-slate-900/80 border border-slate-700 text-white text-xs rounded-xl pl-9 pr-3 py-2 focus:border-sky-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-400 block mb-1">
                  Organization / Municipal Body
                </label>
                <div className="relative">
                  <Building className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="e.g. Brihanmumbai Municipal Corp."
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    className="w-full bg-slate-900/80 border border-slate-700 text-white text-xs rounded-xl pl-9 pr-3 py-2 focus:border-sky-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-400 block mb-1">
                  Account Type
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as UserRole)}
                  className="w-full bg-slate-900/80 border border-slate-700 text-white text-xs rounded-xl px-3 py-2 focus:border-sky-500 focus:outline-none"
                >
                  <option value="customer">🏛️ Customer / Municipal Climate Planner</option>
                  <option value="admin">👑 System Administrator (Full Telemetry)</option>
                </select>
              </div>
            </>
          )}

          <div>
            <label className="text-[11px] font-bold text-slate-400 block mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="email"
                required
                placeholder="user@organization.gov.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900/80 border border-slate-700 text-white text-xs rounded-xl pl-9 pr-3 py-2 focus:border-sky-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-bold text-slate-400 block mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900/80 border border-slate-700 text-white text-xs rounded-xl pl-9 pr-3 py-2 focus:border-sky-500 focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-bold rounded-xl shadow-lg transition-all cursor-pointer"
          >
            {loading ? 'Authenticating...' : tab === 'signin' ? 'Sign In to Dashboard' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
};
