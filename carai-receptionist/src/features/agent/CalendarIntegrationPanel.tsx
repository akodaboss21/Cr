import React, { useState } from 'react';

const providers = [
  { name: 'Google Calendar', description: 'Publish appointments into Google Calendar', enabled: true },
  { name: 'Calendly', description: 'Offer booking links for direct scheduling', enabled: true },
  { name: 'Outlook', description: 'Connect Microsoft 365 calendar events', enabled: false },
];

export default function CalendarIntegrationPanel() {
  const [selected, setSelected] = useState('Google Calendar');

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-slate-900">Calendar integrations</h2>
      <p className="mt-2 text-sm text-slate-600">Connect calendar providers so appointments sync into your workflow automatically.</p>

      <div className="mt-5 space-y-3">
        {providers.map((provider) => (
          <button key={provider.name} onClick={() => setSelected(provider.name)} className={`flex w-full items-start justify-between rounded-2xl border p-4 text-left ${selected === provider.name ? 'border-violet-300 bg-violet-50' : 'border-slate-200 bg-slate-50'}`}>
            <div>
              <p className="font-semibold text-slate-800">{provider.name}</p>
              <p className="mt-1 text-sm text-slate-600">{provider.description}</p>
            </div>
            <span className={`rounded-full px-3 py-1 text-sm font-medium ${provider.enabled ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-200 text-slate-700'}`}>
              {provider.enabled ? 'Enabled' : 'Beta'}
            </span>
          </button>
        ))}
      </div>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
        <p className="font-semibold text-slate-800">Integration hooks</p>
        <p className="mt-2">The app can now surface Google Calendar and Calendly options in the agent area, and the UI is ready for an actual OAuth or API connection layer.</p>
      </div>
    </div>
  );
}
