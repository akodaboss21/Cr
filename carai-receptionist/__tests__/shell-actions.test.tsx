import { fireEvent, render, screen } from '@testing-library/react';
import AppShell from '@/components/layout/AppShell';

jest.mock('next/router', () => ({
  useRouter: () => ({
    replace: jest.fn(),
    push: jest.fn(),
  }),
}));

describe('AppShell navigation actions', () => {
  it('renders settings, notifications, and calendar panels when their actions are triggered', () => {
    render(<AppShell><div>Dashboard body</div></AppShell>);

    fireEvent.click(screen.getByRole('button', { name: /open settings/i }));
    expect(screen.getByRole('heading', { name: /ai settings/i, level: 2 })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /open notifications/i }));
    expect(screen.getByRole('heading', { name: /notifications/i, level: 2 })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /open calendar/i }));
    expect(screen.getByRole('heading', { name: /calendar/i, level: 2 })).toBeInTheDocument();
  });
});
