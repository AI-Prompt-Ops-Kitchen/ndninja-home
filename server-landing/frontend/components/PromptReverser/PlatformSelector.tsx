'use client'

import { Platform } from '@/lib/types'
import { cn } from '@/lib/utils'

interface PlatformOption {
  value: Platform
  label: string
  description: string
}

interface PlatformSelectorProps {
  selectedPlatform: Platform
  onPlatformChange: (platform: Platform) => void
  disabled?: boolean
}

const platforms: PlatformOption[] = [
  {
    value: 'midjourney',
    label: 'Midjourney',
    description: 'Optimized for artistic and stylized imagery',
  },
  {
    value: 'dalle3',
    label: 'DALL-E 3',
    description: 'Best for photorealistic and detailed scenes',
  },
  {
    value: 'flux',
    label: 'Flux',
    description: 'Flexible general-purpose image generation',
  },
  {
    value: 'nanobanana',
    label: 'Nano Banana',
    description: 'Specialized for specific artistic styles',
  },
]

export default function PlatformSelector({
  selectedPlatform,
  onPlatformChange,
  disabled = false,
}: PlatformSelectorProps) {
  return (
    <div className="w-full">
      <label className="block text-sm font-['Inter'] font-medium text-[var(--color-ghost-gray)] mb-3">
        Select Platform
      </label>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {platforms.map((platform) => {
          const isSelected = selectedPlatform === platform.value

          return (
            <button
              key={platform.value}
              type="button"
              onClick={() => onPlatformChange(platform.value)}
              disabled={disabled}
              className={cn(
                'relative p-4 border-2 rounded-lg text-left transition-all',
                'focus:outline-none focus:ring-2 focus:ring-offset-2',
                isSelected
                  ? 'border-[var(--color-tactical-red)] bg-[var(--color-charcoal)] focus:ring-[var(--color-tactical-red)]'
                  : 'border-[var(--color-steel)] bg-[var(--color-shadow-black)] hover:border-[var(--color-tactical-red)] focus:ring-[var(--color-steel)]',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
              style={{
                boxShadow: isSelected ? 'var(--shadow-elevated)' : 'var(--shadow-subtle)'
              }}
            >
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    'mt-0.5 w-5 h-5 rounded-full border-2 flex-shrink-0 transition-all',
                    isSelected
                      ? 'border-[var(--color-tactical-red)] bg-[var(--color-tactical-red)]'
                      : 'border-[var(--color-steel)] bg-[var(--color-deep-charcoal)]'
                  )}
                >
                  {isSelected && (
                    <div className="w-full h-full rounded-full flex items-center justify-center">
                      <div className="w-2 h-2 bg-[var(--color-white)] rounded-full" />
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <p
                    className={cn(
                      'font-["Rajdhani"] font-semibold transition-colors',
                      isSelected ? 'text-[var(--color-white)]' : 'text-[var(--color-ghost-gray)]'
                    )}
                  >
                    {platform.label}
                  </p>
                  <p
                    className={cn(
                      'text-sm font-["Inter"] mt-1 transition-colors',
                      isSelected ? 'text-[var(--color-light-gray)]' : 'text-[var(--color-muted-gray)]'
                    )}
                  >
                    {platform.description}
                  </p>
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
