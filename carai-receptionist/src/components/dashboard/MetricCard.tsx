import React from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  accent?: string;
}

export default function MetricCard({ label, value, icon, accent = 'bg-emerald-400/20 border-emerald-400/40' }: MetricCardProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-700/80 p-6 text-white shadow-md">
      <div className={`absolute right-4 top-4 rounded-xl border p-3 ${accent}`}>
        {icon}
      </div>
      <div className="pt-12">
        <p className="text-sm text-slate-300">{label}</p>
        <p className="mt-2 text-3xl font-semibold">{value}</p>
      </div>
    </div>
  );
}
