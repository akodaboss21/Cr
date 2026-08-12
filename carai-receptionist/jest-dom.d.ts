declare global {
  namespace jest {
    interface Matchers<R = void> {
      toBeInTheDocument(): R;
    }
  }
}

declare module 'react' {
  export function act(callback: () => void): void;
}

export {};
