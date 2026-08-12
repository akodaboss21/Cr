/// <reference types="@testing-library/jest-dom" />
import { render, screen } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import HomePage from '../pages/index';
import { useAuthStore } from '@/lib/auth-store';

jest.mock('next/router', () => ({
  useRouter: () => ({
    replace: jest.fn(),
  }),
}));

describe('Carai dashboard home page', () => {
  beforeEach(() => {
    act(() => {
      useAuthStore.setState({
        isAuthenticated: true,
        user: {
          id: 'local-test-user',
          email: 'test@example.com',
          name: 'Test User',
          provider: 'local',
        },
      });
    });
  });

  afterEach(() => {
    act(() => {
      useAuthStore.setState({
        isAuthenticated: false,
        user: null,
      });
    });
  });

  it('renders the dashboard heading and key metrics', () => {
    render(<HomePage />);

    expect(screen.getByText(/Your AI Receptionist Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Conversations Today/i)).toBeInTheDocument();
    expect(screen.getByText(/Leads Captured/i)).toBeInTheDocument();
  });
});
