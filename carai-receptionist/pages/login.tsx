import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useRouter } from 'next/router';
import { useAuthStore } from '@/lib/auth-store';
import { buildSupabaseAuthUrl } from '@/lib/supabase';

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const navigateTo = (path: string) => {
    if (router) {
      router.push(path);
      return;
    }

    if (typeof window !== 'undefined') {
      window.location.assign(path);
    }
  };

  const onSubmit = (values: FormValues) => {
    login(values.email, values.password, 'local');
    navigateTo('/dashboard');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-12">
      <div className="w-full max-w-md rounded-3xl border border-slate-800 bg-white p-8 shadow-2xl">
        <div className="mb-6 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-violet-600">Carai</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-900">Welcome back</h1>
          <p className="mt-2 text-sm text-slate-600">Sign in with local credentials or continue with Supabase auth.</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="email">Email</label>
            <input id="email" className="w-full rounded-2xl border border-slate-300 px-4 py-3 outline-none ring-0" placeholder="you@example.com" {...register('email')} />
            {errors.email && <p className="mt-2 text-sm text-rose-600">{errors.email.message}</p>}
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="password">Password</label>
            <input id="password" type="password" className="w-full rounded-2xl border border-slate-300 px-4 py-3 outline-none ring-0" placeholder="••••••••" {...register('password')} />
            {errors.password && <p className="mt-2 text-sm text-rose-600">{errors.password.message}</p>}
          </div>

          <button type="submit" className="w-full rounded-2xl bg-violet-600 px-4 py-3 font-semibold text-white transition hover:bg-violet-700">Sign in</button>
        </form>

        <div className="mt-6 space-y-3">
          <a href={buildSupabaseAuthUrl('google')} className="flex items-center justify-center rounded-2xl border border-slate-300 px-4 py-3 text-sm font-medium text-slate-700">Continue with Google</a>
          <a href={buildSupabaseAuthUrl('github')} className="flex items-center justify-center rounded-2xl border border-slate-300 px-4 py-3 text-sm font-medium text-slate-700">Continue with GitHub</a>
        </div>
      </div>
    </div>
  );
}
