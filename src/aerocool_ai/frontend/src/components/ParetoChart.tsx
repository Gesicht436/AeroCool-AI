import React from 'react';
import {
  ResponsiveContainer,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Area,
  ComposedChart,
} from 'recharts';
import { ParetoPoint } from '../types';
import { TrendingUp } from 'lucide-react';

interface ParetoChartProps {
  points: ParetoPoint[];
  currency: 'INR' | 'USD';
  USD_TO_INR: number;
}

export const ParetoChart: React.FC<ParetoChartProps> = ({
  points,
  currency,
  USD_TO_INR,
}) => {
  const chartData = points.map((p) => ({
    ...p,
    costLabel:
      currency === 'INR'
        ? ((p.spent_usd * USD_TO_INR) / 100000).toFixed(1)
        : (p.spent_usd / 1000).toFixed(0),
    cooling: Number(p.mean_cooling_celsius.toFixed(2)),
  }));

  return (
    <div className="glass-panel rounded-2xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-sky-400" />
            Pareto Efficiency Investment Frontier
          </h2>
          <p className="text-xs text-slate-400">
            Multi-budget knapsack frontier mapping capital allocation against temperature relief (°C).
          </p>
        </div>
        <div className="text-xs font-semibold text-sky-400 bg-sky-500/10 border border-sky-400/20 px-3 py-1 rounded-full">
          Diminishing Returns Knee Point Identified
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="coolingGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#38BDF8" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="costLabel"
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              label={{
                value: currency === 'INR' ? 'Capital Invested (₹ Lakhs)' : 'Capital Invested ($k USD)',
                position: 'insideBottom',
                offset: -4,
                fill: '#94A3B8',
                fontSize: 11,
              }}
            />
            <YAxis
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              label={{
                value: 'Mean Cooling (°C)',
                angle: -90,
                position: 'insideLeft',
                fill: '#94A3B8',
                fontSize: 11,
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1E293B',
                borderColor: 'rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#F8FAFC',
                fontSize: '12px',
              }}
            />
            <Area
              type="monotone"
              dataKey="cooling"
              fill="url(#coolingGradient)"
              stroke="#38BDF8"
              strokeWidth={3}
            />
            <Line
              type="monotone"
              dataKey="cooling"
              stroke="#818CF8"
              strokeWidth={2}
              dot={{ r: 5, fill: '#38BDF8', stroke: '#1E293B', strokeWidth: 2 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
