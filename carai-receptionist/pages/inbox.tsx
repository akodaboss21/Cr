import React from 'react';
import AppShell from '@/components/layout/AppShell';

export default function InboxPage() {
  return (
    <AppShell>
      <div className="rounded-2xl border border-slate-200/80 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Inbox</h1>
        <p className="mt-3 text-slate-600">Three-column conversation view and tool traces are scaffolded for the next phase.</p>
      </div>
    </AppShell>
  );
}
