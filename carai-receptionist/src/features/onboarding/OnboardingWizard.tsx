import React, { useMemo, useState } from 'react';

interface StepProps {
  title: string;
  description: string;
  isActive?: boolean;
  isComplete?: boolean;
}

function StepPill({ title, description, isActive = false, isComplete = false }: StepProps) {
  return (
    <div className={`rounded-2xl border px-4 py-3 ${isActive ? 'border-violet-300 bg-violet-50' : isComplete ? 'border-emerald-200 bg-emerald-50' : 'border-slate-200 bg-white'}`}>
      <p className="text-sm font-semibold text-slate-900">{title}</p>
      <p className="mt-1 text-xs text-slate-600">{description}</p>
    </div>
  );
}

export default function OnboardingWizard() {
  const [step, setStep] = useState(1);
  const [businessName, setBusinessName] = useState('A Better Barber');
  const [websiteUrl, setWebsiteUrl] = useState('https://example.com');
  const [knowledgeText, setKnowledgeText] = useState('We are open Monday to Saturday from 9 AM to 7 PM.');
  const [status, setStatus] = useState('Draft');

  const steps = useMemo(() => [
    { title: 'Business info', description: 'Name and intro', complete: step > 1 },
    { title: 'Website', description: 'Brand URL', complete: step > 2 },
    { title: 'Knowledge', description: 'FAQ and policies', complete: step > 3 },
    { title: 'Review', description: 'Check the setup', complete: step > 4 },
  ], [step]);

  const submit = () => {
    if (step < steps.length) {
      setStep((value) => value + 1);
      setStatus(step === steps.length - 1 ? 'Ready to launch' : 'Saved');
      return;
    }

    setStatus('Live');
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="space-y-4">
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-violet-600">Setup</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">Launch your AI receptionist</h2>
          <p className="mt-3 text-sm text-slate-600">Complete the guided steps to connect your business information, website, and knowledge base.</p>
        </div>

        <div className="space-y-3">
          {steps.map((item, index) => (
            <StepPill
              key={item.title}
              title={`${index + 1}. ${item.title}`}
              description={item.description}
              isActive={step === index + 1}
              isComplete={item.complete}
            />
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-900">Step {step} of {steps.length}</p>
            <p className="mt-1 text-sm text-slate-600">{status}</p>
          </div>
          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700">{status}</span>
        </div>

        {step === 1 && (
          <div className="mt-6 space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Business name
              <input value={businessName} onChange={(event) => setBusinessName(event.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none" />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Short intro
              <textarea className="mt-2 h-28 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none" defaultValue="We help customers book services quickly and answer questions instantly." />
            </label>
          </div>
        )}

        {step === 2 && (
          <div className="mt-6 space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Website URL
              <input value={websiteUrl} onChange={(event) => setWebsiteUrl(event.target.value)} className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none" />
            </label>
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
              The wizard will ingest your business details, branding, and site content automatically.
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="mt-6 space-y-4">
            <label className="block text-sm font-medium text-slate-700">
              Knowledge base
              <textarea value={knowledgeText} onChange={(event) => setKnowledgeText(event.target.value)} className="mt-2 h-36 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none" />
            </label>
          </div>
        )}

        {step === 4 && (
          <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
            Review complete. Your receptionist is ready to go live with the provided business profile.
          </div>
        )}

        <div className="mt-8 flex justify-between gap-3">
          <button disabled={step === 1} onClick={() => setStep((value) => Math.max(1, value - 1))} className="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50">Back</button>
          <button onClick={submit} className="rounded-2xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white">{step === steps.length ? 'Launch receptionist' : 'Continue'}</button>
        </div>
      </div>
    </div>
  );
}
