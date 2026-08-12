import React from 'react';

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const slots = [
  ['09:00', '10:00', '11:00'],
  ['13:00', '14:00', '15:00'],
  ['16:00', '17:00', '18:00'],
];

export default function CalendarView() {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-8 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Calendar</h2>
          <p className="mt-2 text-sm text-slate-600">Interactive availability view for the receptionist workspace.</p>
        </div>
        <div className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-sm font-medium text-violet-700">Today</div>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-7">
        {days.map((day) => (
          <div key={day} className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-center text-sm font-semibold text-slate-700">
            {day}
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {slots.map((times, index) => (
          <div key={index} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            {times.map((time) => (
              <div key={time} className="mb-2 rounded-xl border border-violet-200 bg-white px-3 py-2 text-sm text-slate-700">
                {time}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
