import React from 'react';

export default function NotificationsPanel() {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-8 shadow-sm">
      <h2 className="text-xl font-semibold text-slate-900">Notifications</h2>
      <ul className="mt-4 space-y-3 text-sm text-slate-600">
        <li className="rounded-2xl border border-slate-200 bg-slate-50 p-3">New lead assigned from the website widget.</li>
        <li className="rounded-2xl border border-slate-200 bg-slate-50 p-3">Two appointments were rescheduled this morning.</li>
        <li className="rounded-2xl border border-slate-200 bg-slate-50 p-3">Knowledge base sync completed successfully.</li>
      </ul>
    </div>
  );
}
