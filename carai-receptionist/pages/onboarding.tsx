import React from 'react';
import AppShell from '@/components/layout/AppShell';
import OnboardingWizard from '@/features/onboarding/OnboardingWizard';

export default function OnboardingPage() {
  return (
    <AppShell>
      <OnboardingWizard />
    </AppShell>
  );
}
