import React, { useMemo, useState } from 'react';

const initialConversations = [
  {
    id: 'conv-1',
    customer: 'Sarah J.',
    status: 'Ready to confirm',
    summary: 'Asked about a Friday haircut at 3 PM.',
    lastMessage: 'Would you like Friday at 3:00 PM?',
    response: 'Yes, we have a slot available with Stylist Maya.',
  },
  {
    id: 'conv-2',
    customer: 'Alex R.',
    status: 'New lead',
    summary: 'Requested pricing for a premium service package.',
    lastMessage: 'Can I get a quote for the premium package?',
    response: 'Sure! I can share the pricing and availability.',
  },
  {
    id: 'conv-3',
    customer: 'Mina T.',
    status: 'Needs follow-up',
    summary: 'Asked about available stylists for tomorrow.',
    lastMessage: 'Which stylist is open tomorrow morning?',
    response: 'I can book a session with our top stylist at 10 AM.',
  },
];

export default function InboxPanel() {
  const [search, setSearch] = useState('');
  const [selectedConversation, setSelectedConversation] = useState(initialConversations[0]);
  const [filter, setFilter] = useState('all');

  const filteredConversations = useMemo(() => {
    return initialConversations.filter((conversation) => {
      const matchesQuery = conversation.customer.toLowerCase().includes(search.toLowerCase()) || conversation.summary.toLowerCase().includes(search.toLowerCase());
      const matchesFilter = filter === 'all' || conversation.status.toLowerCase().includes(filter);
      return matchesQuery && matchesFilter;
    });
  }, [filter, search]);

  return (
    <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Conversation inbox</h2>
            <p className="mt-2 text-sm text-slate-600">Search, filter, and manage incoming customer conversations.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {['all', 'ready', 'new', 'needs'].map((value) => (
              <button
                key={value}
                onClick={() => setFilter(value)}
                className={`rounded-full border px-3 py-2 text-sm ${filter === value ? 'border-violet-500 bg-violet-50 text-violet-700' : 'border-slate-200 bg-white text-slate-600'}`}
              >
                {value === 'all' ? 'All' : value === 'ready' ? 'Ready' : value === 'new' ? 'New' : 'Follow-up'}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search conversations"
            className="w-full bg-transparent text-sm outline-none"
          />
        </div>

        <div className="space-y-3">
          {filteredConversations.map((conversation) => (
            <button
              key={conversation.id}
              onClick={() => setSelectedConversation(conversation)}
              className={`w-full rounded-2xl border p-4 text-left ${selectedConversation.id === conversation.id ? 'border-violet-300 bg-violet-50' : 'border-slate-200 bg-white'} `}
            >
              <div className="flex items-center justify-between">
                <p className="font-semibold text-slate-800">{conversation.customer}</p>
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold uppercase text-slate-600">{conversation.status}</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">{conversation.summary}</p>
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Conversation details</h2>
            <p className="mt-2 text-sm text-slate-600">Review the current exchange and take over whenever needed.</p>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700">AI handled</span>
        </div>

        <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div>
            <p className="text-sm font-semibold text-slate-800">Customer</p>
            <p className="mt-2 text-sm text-slate-600">{selectedConversation.lastMessage}</p>
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">AI response</p>
            <p className="mt-2 text-sm text-slate-600">{selectedConversation.response}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button className="rounded-full bg-violet-600 px-4 py-2 text-sm font-semibold text-white">Take over conversation</button>
            <button className="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700">Add internal note</button>
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-900">Customer details</h3>
          <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
            <div>
              <p className="font-semibold text-slate-800">Phone</p>
              <p className="mt-1">+1 (555) 123-9876</p>
            </div>
            <div>
              <p className="font-semibold text-slate-800">Email</p>
              <p className="mt-1">{selectedConversation.customer.toLowerCase().replace(' ', '.')}@example.com</p>
            </div>
            <div>
              <p className="font-semibold text-slate-800">Last active</p>
              <p className="mt-1">10 minutes ago</p>
            </div>
            <div>
              <p className="font-semibold text-slate-800">Lead status</p>
              <p className="mt-1">{selectedConversation.status}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
