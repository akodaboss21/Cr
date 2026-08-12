import React, { useState } from 'react';

const initialFaqs = [
  { question: 'What are your opening hours?', answer: 'We are open Monday to Saturday from 9 AM to 7 PM.' },
  { question: 'What is the cancellation policy?', answer: 'Cancel up to 4 hours before your appointment for a full refund.' },
];

const initialServices = ['Haircut', 'Braiding', 'Manicure', 'Facial', 'Product consultation'];

export default function KnowledgePanel() {
  const [faqQuestion, setFaqQuestion] = useState('');
  const [faqAnswer, setFaqAnswer] = useState('');
  const [faqs, setFaqs] = useState(initialFaqs);
  const [knowledgeText, setKnowledgeText] = useState('Our receptionist is trained to answer service, pricing, and availability questions.');
  const [savedState, setSavedState] = useState('Draft');

  return (
    <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
      <div className="space-y-4">
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Knowledge management</h2>
              <p className="mt-2 text-sm text-slate-600">Configure FAQs, services, documents, and training data for your AI receptionist.</p>
            </div>
            <button className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700">Sync knowledge</button>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-800">Add FAQ</p>
              <input value={faqQuestion} onChange={(event) => setFaqQuestion(event.target.value)} className="mt-3 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none" placeholder="Question" />
              <textarea value={faqAnswer} onChange={(event) => setFaqAnswer(event.target.value)} className="mt-3 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none" placeholder="Answer" rows={4} />
              <button className="mt-3 rounded-2xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white" onClick={() => {
                if (faqQuestion && faqAnswer) {
                  setFaqs([...faqs, { question: faqQuestion, answer: faqAnswer }]);
                  setFaqQuestion('');
                  setFaqAnswer('');
                  setSavedState('Updated');
                }
              }}>
                Add FAQ
              </button>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-800">Upload documents</p>
              <p className="mt-2 text-sm text-slate-600">Use documents to enrich the receptionist with business policies, services, and product details.</p>
              <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">
                Drag and drop files here
              </div>
              <button className="mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700">Upload document</button>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Service catalog</h2>
          <div className="mt-4 space-y-3">
            {initialServices.map((service) => (
              <div key={service} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-800">{service}</p>
                <span className="text-xs text-slate-500">Active</span>
              </div>
            ))}
          </div>
          <button className="mt-5 rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white">Add new service</button>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-900">AI knowledge editor</h2>
        <p className="mt-2 text-sm text-slate-600">Edit the receptionist's knowledge base and training prompts for your business.</p>
        <textarea value={knowledgeText} onChange={(event) => setKnowledgeText(event.target.value)} className="mt-5 h-[420px] w-full rounded-3xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-900 outline-none" />
        <div className="mt-4 flex items-center justify-between gap-3">
          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700">{savedState}</span>
          <button className="rounded-2xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white" onClick={() => setSavedState('Saved')}>Save knowledge</button>
        </div>
      </div>
    </div>
  );
}
