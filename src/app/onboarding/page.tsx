"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from '@hookform/resolvers/zod';

// Define the schema for each step
const step1Schema = z.object({
  businessName: z.string().min(1, "Business name is required"),
  email: z.string().email("Invalid email address"),
});

const step2Schema = z.object({
  businessType: z.enum(["Hair Salon", "Barbershop", "Beauty Studio", "Nail Salon", "Retail", "Wholesale"]),
});

const step3Schema = z.object({
  address: z.string().optional(),
  phone: z.string().optional(),
  website: z.string().url().optional(),
  description: z.string().optional(),
});

const step4Schema = z.object({}); // No fields

const step5Schema = z.object({
  faqs: z.string().optional(),
  // Note: file input for documents is not validated via Zod
});

const step6Schema = z.object({}); // No fields

// We'll create a union of all schemas for the form, but we'll validate based on step
// However, react-hook-form with zodResolver expects one schema.
// We can use a schema that is a union of all steps, but then we have to make all fields optional and then refine?
// Alternatively, we can reset the form for each step and use a different resolver.

// Let's do: we'll have a form that we reset when the step changes, and we'll use the schema for the current step.

export default function OnboardingWizard() {
  const [step, setStep] = useState(1);
  const [onboardingId, setOnboardingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [activationStatus, setActivationStatus] = useState<string | null>(null);
  const [widgetCode, setWidgetCode] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors }, reset } = useForm({
    // We'll set the resolver dynamically based on step in a useEffect, but we can't change resolver after init.
    // Instead, we'll use a single schema that is the union of all fields, and we'll validate only the current step's fields by making others optional and then using a custom validate function?
    // Given the complexity, let's use a different approach: we'll have a form for each step and reset when step changes.
    // We'll use the default values and then validate on submit with the step's schema.
    mode: 'onSubmit',
    reValidateMode: 'onChange',
    defaultValues: {
      businessName: '',
      email: '',
      businessType: 'Hair Salon',
      address: '',
      phone: '',
      website: '',
      description: '',
      faqs: '',
    },
  });

  // We'll create a function to validate the current step's data
  const validateStep = (data) => {
    switch (step) {
      case 1:
        return step1Schema.safeParse({ businessName: data.businessName, email: data.email });
      case 2:
        return step2Schema.safeParse({ businessType: data.businessType });
      case 3:
        return step3Schema.safeParse({ address: data.address, phone: data.phone, website: data.website, description: data.description });
      case 4:
        return { success: true }; // No validation
      case 5:
        return step5Schema.safeParse({ faqs: data.faqs });
      case 6:
        return { success: true }; // No validation
      default:
        return { success: false };
    }
  };

  const onSubmit = async (data: any) => {
    setServerError(null);
    const validation = validateStep(data);
    if (!validation.success) {
      // Let client-side errors show
      return;
    }

    setLoading(true);
    try {
      // If we don't yet have an onboarding record, create organization then start onboarding
      if (!onboardingId && step === 1) {
        // create organization
        const orgResp = await fetch('/api/v1/organizations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: data.businessName || data.business_name || 'New Organization' })
        });
        if (!orgResp.ok) throw new Error('Failed to create organization');
        const orgJson = await orgResp.json();

        const startResp = await fetch('/api/v1/onboarding/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ organization_id: orgJson.id })
        });
        if (!startResp.ok) throw new Error('Failed to start onboarding');
        const startJson = await startResp.json();
        setOnboardingId(startJson.id);
        setStep(2);
        return;
      }

      // For subsequent steps, submit step data to the onboarding record
      if (onboardingId) {
        const resp = await fetch(`/api/v1/onboarding/${encodeURIComponent(onboardingId)}/step/${step}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        if (!resp.ok) {
          const txt = await resp.text();
          throw new Error(txt || `Step ${step} submission failed`);
        }
        const updated = await resp.json();
        // If this was the final step, trigger activation
        if (step >= 6) {
          setActivationStatus('activating');
          const actResp = await fetch(`/api/v1/onboarding/${encodeURIComponent(onboardingId)}/activate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          });
          if (!actResp.ok) {
            const txt = await actResp.text();
            throw new Error(txt || 'Activation failed');
          }
          const actJson = await actResp.json();
          setActivationStatus('activated');
          setWidgetCode(actJson.widget_code || null);
        } else {
          setStep((s) => s + 1);
        }
      }
    } catch (err: any) {
      console.error(err);
      setServerError(err?.message || 'Server error');
    } finally {
      setLoading(false);
    }
  };

  // We'll use a key to reset the form when step changes
  const formKey = step.toString();

  return (
    <div className="min-h-screen bg-[#F8FAFC] p-4">
      <div className="max-w-3xl mx-auto">
        {/* Progress Indicator */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex space-x-2">
            {[1, 2, 3, 4, 5, 6].map((num) => (
              <div
                key={num}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  num === step ? "bg-purple-600 text-white" : "bg-gray-200 text-gray-700"
                }`}
              >
                {num}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200/80">
            <h2 className="text-slate-800 text-lg font-medium mb-4">
              Step {step}
            </h2>
            
            <h3 className="text-slate-800 text-md font-medium mb-2">
              {["Welcome", "Business Type", "Business Information", "Services & Products", "Knowledge Base", "AI Configuration"][step - 1]}
            </h3>
            <p className="text-slate-500 mb-4">
              {["Let's set up your AI receptionist", "Select your business category", "Enter your business details", "List your services or products", "Upload FAQs or documents", "Configure your AI receptionist"][step - 1]}
            </p>
            
            <form key={formKey} onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {step === 1 && (
                <div>
                  <div className="mb-4">
                    <label className="block text-slate-700 mb-1">Business Name</label>
                    <input
                      type="text"
                      {...register("businessName")}
                      className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-purple-500"
                    />
                    {errors.businessName && (
                      <p className="text-red-500 text-sm">{errors.businessName.message}</p>
                    )}
                  </div>
                  <div className="mb-4">
                    <label className="block text-slate-700 mb-1">Email</label>
                    <input
                      type="email"
                      {...register("email")}
                      className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-purple-500"
                    />
                    {errors.email && (
                      <p className="text-red-500 text-sm">{errors.email.message}</p>
                    )}
                  </div>
                </div>
              )}
              
              {step === 2 && (
                <div>
                  <div className="space-y-3 mb-4">
                    <label className="block text-slate-700 mb-1">Select Business Type</label>
                    <div className="flex flex-wrap gap-2">
                      {["Hair Salon", "Barbershop", "Beauty Studio", "Nail Salon", "Retail", "Wholesale"].map((type) => (
                        <label key={type} className="flex items-center space-x-2 rounded-md bg-slate-200 px-3 py-2 cursor-pointer hover:bg-gray-100 transition-colors">
                          <span className="text-sm">{type}</span>
                          <input
                            type="radio"
                            {...register("businessType", { value: type })}
                            className="w-4 h-4 text-purple-600 focus:ring-2 focus:ring-purple-500"
                          />
                        </label>
                      ))}
                    </div>
                    {errors.businessType && (
                      <p className="text-red-500 text-sm">{errors.businessType.message}</p>
                    )}
                  </div>
                </div>
              )}
              
              {step === 3 && (
                <div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-slate-700 mb-1">Address</label>
                      <input
                        type="text"
                        {...register("address")}
                        className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-700 mb-1">Phone</label>
                      <input
                        type="tel"
                        {...register("phone")}
                        className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-700 mb-1">Website</label>
                      <input
                        type="url"
                        {...register("website")}
                        className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                  </div>
                  <div className="mb-4">
                    <label className="block text-slate-700 mb-1">Description</label>
                    <textarea
                      {...register("description")}
                      className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-purple-500"
                      rows={3}
                    />
                  </div>
                </div>
              )}
              
              {step === 4 && (
                <div>
                  <p className="text-slate-600 mb-2">Add your main services</p>
                  <div className="space-y-2">
                    {["Haircut", "Coloring", "Styling", "Product Sales"].map((service) => (
                      <div key={service} className="flex items-center space-x-2 bg-white p-3 rounded-lg shadow-sm border border-slate-200/80">
                        <svg className="h-5 w-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/>
                        </svg>
                        <span className="font-medium">{service}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {step === 5 && (
                <div>
                  <div className="mb-4">
                    <label className="block text-slate-700 mb-1">FAQs</label>
                    <textarea
                      {...register("faqs")}
                      className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-purple-500"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-slate-700 mb-1">Documents</label>
                    <input
                      type="file"
                      // We don't register file input with useForm because it's not controlled in the same way
                      // We'll handle it separately if needed, but for now we just leave it unregistered
                    />
                  </div>
                </div>
              )}
              
              {step === 6 && (
                <div>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-slate-700 mb-1">Personality</label>
                      <div className="flex items-center space-x-2">
                        <div className="w-10 h-10 rounded-full border border-slate-300 flex items-center justify-center">
                          <span className="text-sm font-medium">Friendly</span>
                        </div>
                        <span className="text-sm text-slate-700">→</span>
                        <div className="w-10 h-10 rounded-full border border-slate-300 flex items-center justify-center">
                          <span className="font-medium">Professional</span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <label className="block text-slate-700 mb-1">Response Style</label>
                      <div className="flex items-center space-x-2">
                        <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center">
                          <span className="text-xs">Concise</span>
                        </div>
                        <span className="text-sm">→</span>
                        <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center">
                          <span className="text-xs">Detailed</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="flex justify-between pt-4">
                <button
                  type="button"
                  onClick={() => setStep(Math.max(step - 1, 1))}
                  disabled={step === 1}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors disabled:opacity-50"
                >
                  Previous
                </button>
                {step < 6 ? (
                  <button
                    type="submit"
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
                  >
                    Next Step
                  </button>
                ) : (
                  <button
                    type="submit"
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                  >
                    Complete Onboarding
                  </button>
                )}
              </div>
              {/* Server status and activation results */}
              <div className="mt-4">
                {loading && <p className="text-sm text-slate-600">Saving... please wait.</p>}
                {serverError && <p className="text-sm text-red-600">{serverError}</p>}
                {activationStatus === 'activating' && <p className="text-sm text-slate-700">Activating receptionist — generating embeddings and provisioning AI...</p>}
                {activationStatus === 'activated' && widgetCode && (
                  <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3">
                    <p className="text-sm font-semibold text-emerald-800">Activation complete — copy this widget snippet to your site:</p>
                    <pre className="mt-2 overflow-auto text-xs bg-white p-2 rounded">{widgetCode}</pre>
                  </div>
                )}
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}