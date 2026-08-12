import React, { useState } from 'react';

export default function SettingsPanel() {
  const [personality, setPersonality] = useState('Friendly and professional');
  const [greeting, setGreeting] = useState('Hi there! How can I help you today?');
  const [tone, setTone] = useState('Warm and helpful');
  const [escalation, setEscalation] = useState('Prompt human takeover when unsure');
  const [theme, setTheme] = useState('Violet');

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200/80 bg-white p-8 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">AI settings</h2>
            <p className="mt-2 text-sm text-slate-600">Control personality, greeting, tone, and escalation behavior for the receptionist AI.</p>
          </div>
          <button className="rounded-full border border-violet-200 bg-violet-50 px-4 py-2 text-sm font-semibold text-violet-700">Save settings</button>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <label className="text-sm font-semibold text-slate-800">AI personality</label>
            <select value={personality} onChange={(event) => setPersonality(event.target.value)} className="mt-3 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none">
              <option>Friendly and professional</option>
              <option>Concise and direct</option>
              <option>Luxurious and polished</option>
            </select>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <label className="text-sm font-semibold text-slate-800">Greeting message</label>
            <textarea value={greeting} onChange={(event) => setGreeting(event.target.value)} className="mt-3 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none" rows={4} />
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <label className="text-sm font-semibold text-slate-800">Business tone</label>
            <select value={tone} onChange={(event) => setTone(event.target.value)} className="mt-3 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none">
              <option>Warm and helpful</option>
              <option>Professional and polished</option>
              <option>Casual and friendly</option>
            </select>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <label className="text-sm font-semibold text-slate-800">Escalation settings</label>
            <select value={escalation} onChange={(event) => setEscalation(event.target.value)} className="mt-3 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none">
              <option>Prompt human takeover when unsure</option>
              <option>Always route to AI first</option>
              <option>Human takeover only for premium leads</option>
            </select>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-8 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Brand settings</h2>
            <p className="mt-2 text-sm text-slate-600">Upload your logo, preview theme colors, and review the widget appearance.</p>
          </div>
          <button className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700">Upload logo</button>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-800">Logo preview</p>
            <div className="mt-4 flex h-24 items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-white text-sm text-slate-500">No logo uploaded</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-800">Theme preview</p>
            <div className="mt-4 flex items-center gap-2">
              {['Violet', 'Emerald', 'Sky'].map((option) => (
                <button key={option} onClick={() => setTheme(option)} className={`rounded-full px-3 py-2 text-sm font-semibold ${theme === option ? 'bg-violet-600 text-white' : 'bg-white text-slate-700 border border-slate-200'}`}>
                  {option}
                </button>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-800">Widget preview</p>
            <div className="mt-4 rounded-3xl bg-slate-900 p-4 text-sm text-white">
              <p className="font-semibold">Carai reception</p>
              <p className="mt-2 text-xs text-slate-300">Your widget will load with the selected tone and business branding.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
