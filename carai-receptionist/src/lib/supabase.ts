export const supabaseConfig = {
  url: process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://demo.supabase.co',
  anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'demo-anon-key',
};

export function buildSupabaseAuthUrl(provider: 'google' | 'github') {
  const base = `${supabaseConfig.url}/auth/v1/authorize?provider=${provider}`;
  return `${base}&redirect_to=${encodeURIComponent('http://localhost:3000/dashboard')}`;
}
