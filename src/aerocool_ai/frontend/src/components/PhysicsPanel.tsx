import React from 'react';
import { Cpu, Scale, Waves } from 'lucide-react';

export const PhysicsPanel: React.FC = () => {
  return (
    <div className="glass-panel rounded-2xl p-6 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Cpu className="w-5 h-5 text-indigo-400" />
        <h2 className="text-xl font-bold text-white">
          Physics-Informed Machine Learning (PINN) Formulation
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Surface Energy Balance */}
        <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-sky-400 font-bold text-sm">
            <Scale className="w-4 h-4" />
            1. Surface Energy Balance Conservation Law
          </div>
          <div className="bg-slate-950/80 p-3 rounded-lg font-mono text-xs text-sky-300 border border-slate-800 text-center">
            R_n - G - H - λE = 0
          </div>
          <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
            <li>
              <b>Stefan-Boltzmann Net Radiation (R_n)</b>: (1-α)R_sw↓ + εR_lw↓ - εσ(T_s+273.15)⁴
            </li>
            <li>
              <b>Turbulent Sensible Heat Flux (H)</b>: ρ c_p (T_s - T_air) / r_a
            </li>
            <li>
              <b>Latent Heat Flux (λE)</b>: f_v · ET₀(R_n, T_air, u₁₀, RH) ≥ 0
            </li>
            <li>
              <b>Ground Conductive Storage (G)</b>: μ R_n (μ ≈ 0.15 - 0.40)
            </li>
          </ul>
        </div>

        {/* 2D Advection-Diffusion PDE */}
        <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
            <Waves className="w-4 h-4" />
            2. Transient 2D Advection-Diffusion Thermal PDE
          </div>
          <div className="bg-slate-950/80 p-3 rounded-lg font-mono text-xs text-indigo-300 border border-slate-800 text-center">
            ∂T_s/∂t - D ∇²T_s + u · ∇T_s - R_SEB / (ρ C_eff) = 0
          </div>
          <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
            <li>
              <b>PyTorch Autograd Integration</b>: Evaluates exact spatial laplacians ∇²T_s and temporal rates ∂T_s/∂t.
            </li>
            <li>
              <b>Random Fourier Features (RFF)</b>: Overcomes spectral bias when resolving narrow street canyons and building edges.
            </li>
            <li>
              <b>Softplus Latent Constraint</b>: Enforces non-negative evapotranspiration λE ≥ 0 inside neural decoders.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
