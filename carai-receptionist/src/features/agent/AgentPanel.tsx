import React from 'react';
import CalendarIntegrationPanel from './CalendarIntegrationPanel';

const toggles = [
  { label: 'Casual tone', enabled: true },
  { label: 'Appointment booking', enabled: true },
  { label: 'Lead capture', enabled: true },
  { label: 'Fallback to human', enabled: false },
];

export default function AgentPanel() {
  return (
    <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="space-y-4">
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Personality & capabilities</h2>
          <div className="mt-4 space-y-3">
            {toggles.map((toggle) => (
              <div key={toggle.label} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="font-semibold text-slate-800">{toggle.label}</p>
                <span className={`rounded-full px-3 py-1 text-sm font-medium ${toggle.enabled ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-200 text-slate-700'}`}>{toggle.enabled ? 'On' : 'Off'}</span>
              </div>
            ))}
          </div>
        </div>

        <CalendarIntegrationPanel />
      </div>

      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Provider stack</h2>
        <p className="mt-3 text-sm text-slate-600">OpenAI-compatible gateway with fallback enabled for Ollama and local endpoints.</p>
      </div>
    </div>
  );
}
