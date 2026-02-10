'use client'

import { useState } from 'react'
import { AnalysisResult } from '@/lib/types'
import {
  ClipboardIcon,
  CheckIcon,
  SparklesIcon,
  SwatchIcon,
  RectangleStackIcon
} from '@heroicons/react/24/outline'
import { cn } from '@/lib/utils'

interface ResultsDisplayProps {
  result: AnalysisResult
}

export default function ResultsDisplay({ result }: ResultsDisplayProps) {
  const [copiedPrompt, setCopiedPrompt] = useState<string | null>(null)

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedPrompt(id)
      setTimeout(() => setCopiedPrompt(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="w-full space-y-6">
      {/* Header with confidence score */}
      <div className="flex items-center justify-between pb-4 border-b border-[var(--color-steel)]">
        <h2 className="text-2xl font-['Rajdhani'] font-bold text-[var(--color-white)]">Analysis Results</h2>
        <div className="flex items-center gap-2">
          <span className="text-sm font-['Inter'] text-[var(--color-muted-gray)]">Confidence:</span>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--color-charcoal)] border border-[var(--color-steel)] rounded-lg">
            <div className={cn(
              "w-2 h-2 rounded-full",
              result.confidence_score >= 0.8 ? "bg-[var(--color-online)]" :
              result.confidence_score >= 0.6 ? "bg-yellow-500" :
              "bg-[var(--color-target-red)]"
            )} />
            <span className="text-sm font-['JetBrains_Mono'] font-semibold text-[var(--color-white)]">
              {(result.confidence_score * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Main Prompt */}
      <div className="bg-[var(--color-charcoal)] border border-[var(--color-tactical-red)] rounded-lg p-6"
        style={{ boxShadow: '0 0 20px rgba(153, 27, 27, 0.2)' }}
      >
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex items-center gap-2">
            <SparklesIcon className="w-5 h-5 text-[var(--color-tactical-red)]" />
            <h3 className="text-lg font-['Rajdhani'] font-semibold text-[var(--color-white)]">Main Prompt</h3>
          </div>
          <button
            onClick={() => copyToClipboard(result.main_prompt, 'main')}
            className="p-2 hover:bg-[var(--color-steel)]/20 rounded-lg transition-colors"
            title="Copy to clipboard"
          >
            {copiedPrompt === 'main' ? (
              <CheckIcon className="w-5 h-5 text-[var(--color-online)]" />
            ) : (
              <ClipboardIcon className="w-5 h-5 text-[var(--color-light-gray)]" />
            )}
          </button>
        </div>
        <p className="text-[var(--color-ghost-gray)] font-['Inter'] leading-relaxed">{result.main_prompt}</p>
      </div>

      {/* Prompt Variations */}
      {result.variations && result.variations.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-['Rajdhani'] font-semibold text-[var(--color-white)] flex items-center gap-2">
            <RectangleStackIcon className="w-5 h-5 text-[var(--color-tactical-red)]" />
            Alternative Prompts
          </h3>
          <div className="space-y-2">
            {result.variations.map((variation, index) => (
              <div
                key={index}
                className="bg-[var(--color-shadow-black)] border border-[var(--color-steel)] rounded-lg p-4 hover:border-[var(--color-tactical-red)] transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="text-[var(--color-light-gray)] font-['Inter'] leading-relaxed">{variation.prompt}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex-1 bg-[var(--color-deep-charcoal)] rounded-full h-1.5">
                        <div
                          className="bg-gradient-to-r from-[var(--color-tactical-red)] to-[var(--color-target-red)] h-1.5 rounded-full transition-all"
                          style={{ width: `${variation.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-['JetBrains_Mono'] text-[var(--color-muted-gray)] font-medium min-w-[3rem] text-right">
                        {(variation.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => copyToClipboard(variation.prompt, `var-${index}`)}
                    className="p-2 hover:bg-[var(--color-steel)]/20 rounded-lg transition-colors flex-shrink-0"
                    title="Copy to clipboard"
                  >
                    {copiedPrompt === `var-${index}` ? (
                      <CheckIcon className="w-4 h-4 text-[var(--color-online)]" />
                    ) : (
                      <ClipboardIcon className="w-4 h-4 text-[var(--color-light-gray)]" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Negative Prompt */}
      {result.negative_prompt && (
        <div className="bg-[var(--color-shadow-black)] border border-[var(--color-target-red)]/50 rounded-lg p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <h3 className="text-sm font-['Rajdhani'] font-semibold text-[var(--color-target-red)] mb-2">Negative Prompt</h3>
              <p className="text-sm font-['Inter'] text-[var(--color-light-gray)] leading-relaxed">{result.negative_prompt}</p>
            </div>
            <button
              onClick={() => copyToClipboard(result.negative_prompt!, 'negative')}
              className="p-2 hover:bg-[var(--color-steel)]/20 rounded-lg transition-colors flex-shrink-0"
              title="Copy to clipboard"
            >
              {copiedPrompt === 'negative' ? (
                <CheckIcon className="w-4 h-4 text-[var(--color-online)]" />
              ) : (
                <ClipboardIcon className="w-4 h-4 text-[var(--color-light-gray)]" />
              )}
            </button>
          </div>
        </div>
      )}

      {/* Style Analysis */}
      {result.style_analysis && result.style_analysis.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-['Rajdhani'] font-semibold text-[var(--color-white)] flex items-center gap-2">
            <SwatchIcon className="w-5 h-5 text-[var(--color-tactical-red)]" />
            Style Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {result.style_analysis.map((style, index) => (
              <div
                key={index}
                className="bg-[var(--color-charcoal)] border border-[var(--color-steel)] rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <p className="font-['Inter'] font-medium text-[var(--color-white)]">{style.style}</p>
                  <span className="text-sm font-['JetBrains_Mono'] text-[var(--color-tactical-red)]">
                    {(style.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="bg-[var(--color-deep-charcoal)] rounded-full h-1.5">
                  <div
                    className="bg-gradient-to-r from-[var(--color-tactical-red)] to-[var(--color-target-red)] h-1.5 rounded-full transition-all"
                    style={{ width: `${style.confidence * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Composition Analysis */}
      {result.composition_analysis && (
        <div className="bg-[var(--color-charcoal)] border border-[var(--color-steel)] rounded-lg p-4">
          <h3 className="text-lg font-['Rajdhani'] font-semibold text-[var(--color-white)] mb-3">Composition</h3>
          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <span className="text-sm font-['Inter'] font-medium text-[var(--color-muted-gray)] min-w-[6rem]">Type:</span>
              <span className="text-sm font-['Inter'] text-[var(--color-white)]">{result.composition_analysis.composition_type}</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-sm font-['Inter'] font-medium text-[var(--color-muted-gray)] min-w-[6rem]">Aspect:</span>
              <span className="text-sm font-['Inter'] text-[var(--color-white)]">{result.composition_analysis.aspect}</span>
            </div>
            {result.composition_analysis.elements && result.composition_analysis.elements.length > 0 && (
              <div className="flex items-start gap-2">
                <span className="text-sm font-['Inter'] font-medium text-[var(--color-muted-gray)] min-w-[6rem]">Elements:</span>
                <div className="flex flex-wrap gap-1.5">
                  {result.composition_analysis.elements.map((element, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-[var(--color-shadow-black)] border border-[var(--color-steel)] text-[var(--color-light-gray)] text-xs font-['JetBrains_Mono'] rounded-full"
                    >
                      {element}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Processing time */}
      <div className="text-center text-sm font-['JetBrains_Mono'] text-[var(--color-muted-gray)] pt-4 border-t border-[var(--color-steel)]">
        Processed in {result.processing_time.toFixed(2)}s
      </div>
    </div>
  )
}
