interface ProgressRingProps {
  percent: number;
  label: string;
  accent: 'purple' | 'emerald' | 'slate' | 'sky' | 'violet' | 'amber';
}

const colors = {
  purple: '#8b5cf6',
  emerald: '#34d399',
  slate: '#64748b',
  sky: '#38bdf8',
  violet: '#7c3aed',
  amber: '#f59e0b',
};

export default function ProgressRing({ percent, label, accent }: ProgressRingProps) {
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;
  const ringColor = colors[accent];

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative flex h-24 w-24 items-center justify-center">
        <svg viewBox="0 0 100 100" className="h-24 w-24 -rotate-90">
          <circle cx="50" cy="50" r={radius} stroke="#e2e8f0" strokeWidth="8" fill="none" />
          <circle
            cx="50"
            cy="50"
            r={radius}
            stroke={ringColor}
            strokeWidth="8"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute text-center">
          <p className="text-lg font-semibold text-slate-800">{percent}%</p>
        </div>
      </div>
      <p className="text-center text-sm font-medium text-slate-600">{label}</p>
    </div>
  );
}
