'use client'

import { cn } from '@/lib/utils'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface AnalysisStatusProps {
  status: 'idle' | 'analyzing' | 'success' | 'error'
  error?: string | null
  progress?: number
}

export default function AnalysisStatus({ status, error, progress }: AnalysisStatusProps) {
  if (status === 'idle') {
    return null
  }

  if (status === 'analyzing') {
    return (
      <div className="w-full bg-[var(--color-shadow-black)] border border-[var(--color-steel)] rounded-lg p-6"
        style={{ boxShadow: 'var(--shadow-subtle)' }}
      >
        <div className="flex flex-col items-center gap-4">
          {/* Spinner */}
          <div className="relative w-16 h-16">
            <div className="absolute inset-0 border-4 border-[var(--color-steel)] rounded-full" />
            <div className="absolute inset-0 border-4 border-[var(--color-tactical-red)] rounded-full border-t-transparent animate-spin" />
          </div>

          {/* Status text */}
          <div className="text-center">
            <p className="text-lg font-['Rajdhani'] font-bold text-[var(--color-white)]">
              Analyzing Image...
            </p>
            <p className="text-sm font-['Inter'] text-[var(--color-light-gray)] mt-1">
              This may take a few moments
            </p>
          </div>

          {/* Progress bar */}
          {progress !== undefined && (
            <div className="w-full max-w-md">
              <div className="bg-[var(--color-deep-charcoal)] rounded-full h-2 overflow-hidden border border-[var(--color-steel)]">
                <div
                  className="bg-gradient-to-r from-[var(--color-tactical-red)] to-[var(--color-target-red)] h-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs font-['JetBrains_Mono'] text-[var(--color-light-gray)] text-center mt-2">
                {progress}% complete
              </p>
            </div>
          )}
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="w-full bg-[var(--color-shadow-black)] border-2 border-[var(--color-target-red)] rounded-lg p-6"
        style={{ boxShadow: '0 0 20px rgba(220, 38, 38, 0.2)' }}
      >
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <div className="p-2 bg-[var(--color-target-red)]/20 rounded-full border border-[var(--color-target-red)]">
              <ExclamationTriangleIcon className="w-6 h-6 text-[var(--color-target-red)]" />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-['Rajdhani'] font-bold text-[var(--color-white)] mb-1">
              Analysis Failed
            </h3>
            <p className="text-sm font-['Inter'] text-[var(--color-light-gray)] leading-relaxed">
              {error || 'An unexpected error occurred. Please try again.'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return null
}
