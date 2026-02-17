'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { hapticSlide, hapticTap } from '@/lib/haptics';
import { SpikeType } from '@/types/spike';

interface IntensitySliderProps {
  value: number;
  onChange: (value: number) => void;
  type: SpikeType | null;
}

const labels = ['', 'Mild', 'Low', 'Medium', 'High', 'Intense'];

export function IntensitySlider({ value, onChange, type }: IntensitySliderProps) {
  const isViolet = type === 'anxiety';
  const [bouncingDot, setBouncingDot] = useState<number | null>(null);

  const handleDotClick = (n: number) => {
    hapticTap();
    setBouncingDot(n);
    onChange(n);
    setTimeout(() => setBouncingDot(null), 350);
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVal = Number(e.target.value);
    if (newVal !== value) hapticSlide();
    onChange(newVal);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-400">Intensity</span>
        <span
          className={cn(
            'text-sm font-semibold px-3 py-1 rounded-full transition-all',
            isViolet
              ? 'text-violet-300 bg-violet-600/15'
              : 'text-sky-300 bg-sky-600/15'
          )}
        >
          {value} — {labels[value]}
        </span>
      </div>

      <input
        type="range"
        min={1}
        max={5}
        step={1}
        value={value}
        onChange={handleSliderChange}
        className="w-full"
        style={{
          accentColor: isViolet ? '#8b5cf6' : '#0ea5e9',
        }}
      />

      <div className="flex justify-between px-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => handleDotClick(n)}
            className={cn(
              'w-9 h-9 rounded-full text-xs font-bold transition-all',
              bouncingDot === n && 'animate-stim-bounce',
              value === n
                ? isViolet
                  ? 'bg-violet-600 text-white shadow-[0_0_12px_rgba(139,92,246,0.4)]'
                  : 'bg-sky-600 text-white shadow-[0_0_12px_rgba(14,165,233,0.4)]'
                : 'bg-gray-800 text-gray-500 hover:bg-gray-700'
            )}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}
