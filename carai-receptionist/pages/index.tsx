import React, { useMemo } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import AppShell from '@/components/layout/AppShell';
import MetricCard from '@/components/dashboard/MetricCard';
import ProgressRing from '@/components/dashboard/ProgressRing';
import { BarChart3, Bot, CalendarCheck2, MessageCircleMore, PieChart, Send, Sparkles, UserRoundPlus, Users } from 'lucide-react';
import ProtectedRoute from '@/components/layout/ProtectedRoute';
import { useAuthStore } from '@/lib/auth-store';

type RingAccent = 'purple' | 'emerald' | 'slate' | 'sky' | 'violet' | 'amber';

const dashboardMetrics = [
  { label: 'Conversations Today', value: '128', icon: <MessageCircleMore className="h-5 w-5 text-emerald-300" />, accent: 'bg-emerald-400/20 border-emerald-400/40' },
  { label: 'Leads Captured', value: '34', icon: <UserRoundPlus className="h-5 w-5 text-violet-300" />, accent: 'bg-violet-400/20 border-violet-400/40' },
  { label: 'Bookings', value: '18', icon: <CalendarCheck2 className="h-5 w-5 text-sky-300" />, accent: 'bg-sky-400/20 border-sky-400/40' },
  { label: 'AI Resolution Rate', value: '94.2%', icon: <PieChart className="h-5 w-5 text-amber-300" />, accent: 'bg-amber-400/20 border-amber-400/40' },
  { label: 'Active Customers', value: '92', icon: <Users className="h-5 w-5 text-slate-300" />, accent: 'bg-slate-400/20 border-slate-400/40' },
];

const onboardingSteps: { title: string; percent: number; accent: RingAccent }[] = [
  { title: 'Profile completed', percent: 90, accent: 'purple' },
  { title: 'Knowledge added', percent: 70, accent: 'emerald' },
  { title: 'Services listed', percent: 55, accent: 'sky' },
  { title: 'Widget installed', percent: 20, accent: 'violet' },
  { title: 'AI tested', percent: 15, accent: 'amber' },
];

const activityItems = [
  { title: 'Incoming message from widget', subtitle: 'Morgan R.', timestamp: '2m ago', badge: 'bg-emerald-50 text-emerald-600', icon: <MessageCircleMore className="h-4 w-4" /> },
  { title: 'Lead captured', subtitle: 'Widget form', timestamp: '5m ago', badge: 'bg-violet-50 text-violet-600', icon: <UserRoundPlus className="h-4 w-4" /> },
  { title: 'Booking confirmed', subtitle: 'Haircut with Mark', timestamp: '18m ago', badge: 'bg-sky-50 text-sky-600', icon: <CalendarCheck2 className="h-4 w-4" /> },
  { title: 'AI answer refined', subtitle: 'Knowledge base updated', timestamp: '1h ago', badge: 'bg-amber-50 text-amber-600', icon: <Sparkles className="h-4 w-4" /> },
];

const analyticsCards = [
  { label: 'Conversation volume', value: '512', detail: 'Up 12% from last week' },
  { label: 'Lead conversion', value: '24%', detail: 'On track to exceed target' },
  { label: 'Booking conversion', value: '18%', detail: 'Steady growth' },
  { label: 'Popular FAQ', value: 'Availability', detail: 'Most asked topic' },
];

export default function HomePage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  React.useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, router]);

  const onboardingProgress = useMemo(() => {
    const completed = onboardingSteps.filter((step) => step.percent >= 50).length;
    return `${completed} of ${onboardingSteps.length} complete`;
  }, []);

  return (
    <>
      <Head>
        <title>Carai Receptionist Dashboard</title>
        <meta name="description" content="Carai AI Receptionist dashboard for business owners" />
      </Head>
      <ProtectedRoute>
        <AppShell>
          <div className="space-y-6">
            <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
              <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div>
                  <h1 className="text-2xl font-semibold text-slate-900">Business overview</h1>
                  <p className="mt-2 text-sm text-slate-600">Monitor conversations, leads, bookings, and AI performance in one dashboard.</p>
                </div>
                <div className="inline-flex items-center gap-3 rounded-full border border-violet-200 bg-violet-50 px-4 py-2 text-sm font-medium text-violet-700">
                  <Sparkles className="h-4 w-4" /> Demo business mode
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
                {dashboardMetrics.map((metric) => (
                  <MetricCard key={metric.label} {...metric} />
                ))}
              </div>
            </section>

            <div className="grid gap-6 xl:grid-cols-[1.4fr_0.6fr]">
              <div className="space-y-6">
                <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
                  <div className="mb-5 flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-slate-900">Onboarding checklist</h2>
                      <p className="mt-2 text-sm text-slate-600">Finish setup steps that unlock more leads and bookings.</p>
                    </div>
                    <span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-sm font-medium text-violet-700">{onboardingProgress}</span>
                  </div>
                  <div className="grid gap-4 lg:grid-cols-3">
                    {onboardingSteps.map((step) => (
                      <ProgressRing key={step.title} percent={step.percent} label={step.title} accent={step.accent} />
                    ))}
                  </div>
                </section>

                <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
                  <div className="mb-5 flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-slate-900">Analytics highlights</h2>
                      <p className="mt-2 text-sm text-slate-600">Keep an eye on the data that matters most for business growth.</p>
                    </div>
                    <button className="rounded-full border border-slate-200 px-3 py-1 text-sm text-slate-600">View report</button>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {analyticsCards.map((card) => (
                      <div key={card.label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <p className="text-sm font-semibold text-slate-700">{card.label}</p>
                        <p className="mt-3 text-3xl font-semibold text-slate-900">{card.value}</p>
                        <p className="mt-2 text-sm text-slate-500">{card.detail}</p>
                      </div>
                    ))}
                  </div>
                </section>
              </div>

              <aside className="space-y-6">
                <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
                  <div className="mb-5 flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-slate-900">Live demo business</h2>
                      <p className="mt-2 text-sm text-slate-600">Preview the receptionist experience before connecting your live business.</p>
                    </div>
                    <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700">Preview</span>
                  </div>
                  <div className="space-y-4 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-center justify-between rounded-2xl bg-white p-4">
                      <div>
                        <p className="text-sm font-semibold text-slate-900">A Better Barber</p>
                        <p className="text-xs text-slate-500">Demo business</p>
                      </div>
                      <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">Active</span>
                    </div>
                    <div className="grid gap-3">
                      <div className="rounded-2xl border border-slate-200 bg-white p-4">
                        <p className="text-sm text-slate-500">Widget status</p>
                        <p className="mt-2 font-semibold text-slate-900">Installed</p>
                      </div>
                      <div className="rounded-2xl border border-slate-200 bg-white p-4">
                        <p className="text-sm text-slate-500">AI greeting</p>
                        <p className="mt-2 font-semibold text-slate-900">Friendly and professional</p>
                      </div>
                    </div>
                  </div>
                </section>

                <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
                  <div className="mb-5 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-slate-900">Recent activity</h2>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">Live</span>
                  </div>
                  <div className="space-y-3">
                    {activityItems.map((item) => (
                      <div key={item.title} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <div className={`rounded-xl p-2 ${item.badge}`}>{item.icon}</div>
                            <div>
                              <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                              <p className="text-xs text-slate-500">{item.subtitle}</p>
                            </div>
                          </div>
                          <p className="text-xs text-slate-500">{item.timestamp}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </aside>
            </div>
          </div>
        </AppShell>
      </ProtectedRoute>
    </>
  );
}
