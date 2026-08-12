import React from 'react';

const customer = {
  name: 'Jordan P.',
  status: 'Qualified lead',
  phone: '+1 (555) 214-8790',
  email: 'jordan.p@example.com',
  recentVisits: '2 weeks ago',
  lifetimeValue: '$1,240',
  bookings: [
    { date: 'Aug 8', service: 'Haircut', status: 'Confirmed' },
    { date: 'Jul 29', service: 'Facial', status: 'Completed' },
  ],
  notes: [
    { date: 'Aug 6', text: 'Prefers text confirmation and afternoon appointments.' },
    { date: 'Jul 29', text: 'Requested premium styling for next visit.' },
  ],
};

export default function CrmPanel() {
  return (
    <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
      <div className="space-y-4">
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Customer profile</h2>
              <p className="mt-2 text-sm text-slate-600">Review customer history, bookings, notes, and lead status.</p>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700">{customer.status}</span>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Phone</p>
              <p className="mt-2 font-semibold text-slate-900">{customer.phone}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Email</p>
              <p className="mt-2 font-semibold text-slate-900">{customer.email}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Lifetime value</p>
              <p className="mt-2 font-semibold text-slate-900">{customer.lifetimeValue}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Recent visit</p>
              <p className="mt-2 font-semibold text-slate-900">{customer.recentVisits}</p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Booking history</h2>
          <div className="mt-4 space-y-3">
            {customer.bookings.map((booking) => (
              <div key={booking.date} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-slate-800">{booking.service}</p>
                    <p className="text-sm text-slate-500">{booking.date}</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{booking.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Notes & actions</h2>
          <div className="mt-4 space-y-3">
            {customer.notes.map((note) => (
              <div key={note.date} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                <p className="font-semibold text-slate-800">{note.date}</p>
                <p className="mt-1">{note.text}</p>
              </div>
            ))}
          </div>
          <button className="mt-6 w-full rounded-2xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white">Add note</button>
        </div>

        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Lead status</h2>
          <p className="mt-3 text-sm text-slate-600">This customer is a qualified lead. Use the messaging workflow to close their next booking.</p>
          <div className="mt-5 space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-800">Lead score</p>
              <p className="font-semibold text-slate-900">82</p>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-800">Next follow-up</p>
              <p className="font-semibold text-slate-900">Tomorrow</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
