import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import OnboardingWizard from '@/features/onboarding/OnboardingWizard';

describe('OnboardingWizard', () => {
  it('advances through the wizard steps', () => {
    render(<OnboardingWizard />);

    expect(screen.getByText(/Step 1 of 4/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    expect(screen.getByText(/Step 2 of 4/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    expect(screen.getByText(/Step 3 of 4/i)).toBeInTheDocument();
  });
});
