import React, { ReactNode, useState } from 'react';
import { useRouter } from 'next/router';
import { Bell, CalendarDays, ChevronLeft, LayoutGrid, MessageSquareText, Settings, Users, BookOpen, Bot, LogOut, Sparkles } from 'lucide-react';
import SettingsPanel from '@/features/settings/SettingsPanel';
import NotificationsPanel from '@/features/notifications/NotificationsPanel';
import CalendarView from '@/features/calendar/CalendarView';
import InboxPanel from '@/features/inbox/InboxPanel';
import CrmPanel from '@/features/crm/CrmPanel';
import CalendarPanel from '@/features/appointments/CalendarPanel';
import KnowledgePanel from '@/features/knowledge/KnowledgePanel';
import AgentPanel from '@/features/agent/AgentPanel';
import { useAuthStore } from '@/lib/auth-store';

interface AppShellProps {
  children: ReactNode;
}

type ViewKey = 'dashboard' | 'inbox' | 'crm' | 'appointments' | 'knowledge' | 'agent' | 'settings' | 'notifications' | 'calendar';

const navItems: Array<{ icon: typeof LayoutGrid; label: string; key: ViewKey }> = [
  { icon: LayoutGrid, label: 'Dashboard', key: 'dashboard' },
  { icon: MessageSquareText, label: 'Inbox', key: 'inbox' },
  { icon: Users, label: 'CRM', key: 'crm' },
  { icon: CalendarDays, label: 'Appointments', key: 'appointments' },
  { icon: BookOpen, label: 'Knowledge', key: 'knowledge' },
  { icon: Bot, label: 'Agent Setup', key: 'agent' },
];

export default function AppShell({ children }: AppShellProps) {
  const router = useRouter();
  const logout = useAuthStore((state) => state.logout);
  const [collapsed, setCollapsed] = useState(false);
  const [activeView, setActiveView] = useState<ViewKey>('dashboard');

  const navigateTo = (path: string) => {
    if (router) {
      router.replace(path);
      return;
    }

    if (typeof window !== 'undefined') {
      window.location.assign(path);
    }
  };

  const renderSectionTitle = () => {
    switch (activeView) {
      case 'inbox':
        return 'Inbox';
      case 'crm':
        return 'CRM';
      case 'appointments':
        return 'Appointments';
      case 'knowledge':
        return 'Knowledge';
      case 'agent':
        return 'Agent Setup';
      case 'settings':
        return 'Settings';
      case 'notifications':
        return 'Notifications';
      case 'calendar':
        return 'Calendar';
      default:
        return 'Your AI Receptionist Dashboard';
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="flex min-h-screen">
        <aside className={`flex flex-col justify-between bg-slate-950 px-4 py-6 text-slate-100 transition-all ${collapsed ? 'w-24' : 'w-72'}`}>
          <div>
            <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-lg shadow-violet-500/30">
                  <Sparkles className="h-5 w-5" />
                </div>
                {!collapsed && <div>
                  <p className="text-lg font-semibold">Carai</p>
                  <p className="text-xs text-slate-400">AI Receptionist</p>
                </div>}
              </div>
              <button onClick={() => setCollapsed((value) => !value)} className="rounded-full border border-slate-800 p-2 text-slate-400 hover:text-white">
                <ChevronLeft className={`h-4 w-4 transition-transform ${collapsed ? 'rotate-180' : ''}`} />
              </button>
            </div>

            <div className="mt-8 space-y-2">
              {navItems.map(({ icon: Icon, label, key }) => {
                const isActive = activeView === key;
                return (
                  <button key={label} onClick={() => setActiveView(key)} className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-sm transition ${isActive ? 'border border-violet-500/40 bg-slate-800/90 shadow-sm shadow-violet-900/20' : 'text-slate-400 hover:bg-slate-900 hover:text-white'}`}>
                    <Icon className="h-4 w-4" />
                    {!collapsed && <span>{label}</span>}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <button aria-label="Open settings" onClick={() => setActiveView('settings')} className="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-sm text-slate-400 hover:bg-slate-900 hover:text-white">
              <Settings className="h-4 w-4" />
              {!collapsed && <span>Settings</span>}
            </button>
            <button
              type="button"
              onClick={() => {
                logout();
                navigateTo('/login');
              }}
              className="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-sm text-slate-400 hover:bg-slate-900 hover:text-white"
            >
              <LogOut className="h-4 w-4" />
              {!collapsed && <span>Logout</span>}
            </button>
          </div>
        </aside>

        <main className="flex-1 bg-[#f8fafc] p-6 lg:p-8">
          <div className="mx-auto max-w-7xl">
            <header className="mb-6 flex items-center justify-between rounded-2xl border border-slate-200/80 bg-white/80 px-5 py-4 shadow-sm backdrop-blur">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-400">Operations</p>
                <h1 className="text-2xl font-semibold text-slate-900">{renderSectionTitle()}</h1>
              </div>
              <div className="flex items-center gap-3">
                <button aria-label="Open calendar" onClick={() => setActiveView('calendar')} className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 shadow-sm">
                  <CalendarDays className="h-5 w-5" />
                </button>
                <button aria-label="Open notifications" onClick={() => setActiveView('notifications')} className="relative rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 shadow-sm">
                  <Bell className="h-5 w-5" />
                  <span className="absolute right-1 top-1 h-2.5 w-2.5 rounded-full bg-rose-500" />
                </button>
                <div className="flex items-center gap-3 rounded-full border border-slate-200 bg-slate-50 px-2 py-1.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 text-sm font-semibold text-white">AJ</div>
                  <div className="pr-1">
                    <p className="text-sm font-semibold text-slate-800">Alicia</p>
                    <p className="text-xs text-slate-500">Owner</p>
                  </div>
                </div>
              </div>
            </header>

            {activeView === 'dashboard' ? children : activeView === 'settings' ? <SettingsPanel /> : activeView === 'notifications' ? <NotificationsPanel /> : activeView === 'calendar' ? <CalendarView /> : activeView === 'inbox' ? <InboxPanel /> : activeView === 'crm' ? <CrmPanel /> : activeView === 'appointments' ? <CalendarPanel /> : activeView === 'knowledge' ? <KnowledgePanel /> : activeView === 'agent' ? <AgentPanel /> : (
              <div className="rounded-2xl border border-slate-200/80 bg-white p-8 shadow-sm">
                <h2 className="text-xl font-semibold text-slate-900">{renderSectionTitle()}</h2>
                <p className="mt-3 text-slate-600">This view is now active and ready for the full feature module implementation.</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
