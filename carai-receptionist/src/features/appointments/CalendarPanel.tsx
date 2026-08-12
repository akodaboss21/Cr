import React from 'react';

const events = [
  { time: '09:00', title: 'Haircut booking', client: 'Sarah J.' },
  { time: '11:30', title: 'Consultation', client: 'Alex R.' },
  { time: '15:00', title: 'Premium package', client: 'Mina T.' },
];

export default function CalendarPanel() {
  return (
    <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-900">Today’s schedule</h2>
        <div className="mt-4 space-y-3">
          {events.map((event) => (
            <div key={event.time} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div>
                <p className="font-semibold text-slate-800">{event.title}</p>
                <p className="text-sm text-slate-500">{event.client}</p>
              </div>
              <span className="rounded-full bg-sky-50 px-3 py-1 text-sm font-medium text-sky-700">{event.time}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Availability</h2>
        <p className="mt-3 text-sm text-slate-600">3 windows available before 6 PM. The receptionist can auto-offer them in chat.</p>
      </div>
    </div>
  );
}
