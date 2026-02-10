'use client'

import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { usePromptReverserStore } from '@/stores/usePromptReverserStore'
import { useServiceStatusStore } from '@/stores/useServiceStatusStore'
import ImageUpload from '@/components/PromptReverser/ImageUpload'
import PlatformSelector from '@/components/PromptReverser/PlatformSelector'
import ResultsDisplay from '@/components/PromptReverser/ResultsDisplay'
import AnalysisStatus from '@/components/PromptReverser/AnalysisStatus'
import ServiceGrid from '@/components/ServiceGrid/ServiceGrid'
import StatusDashboard from '@/components/ServerStatus/StatusDashboard'
import TacticalGrid from '@/components/Background/AnimatedGrid'
import { SparklesIcon, ServerStackIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'

export default function Home() {
  // Prompt Reverser state
  const {
    selectedFile,
    selectedPlatform,
    status,
    error,
    result,
    progress,
    setSelectedFile,
    setSelectedPlatform,
    analyzeImage,
    reset
  } = usePromptReverserStore()

  // Service status state
  const {
    services,
    systemMetrics,
    isConnected,
    isConnecting,
    connect,
    disconnect
  } = useServiceStatusStore()

  // Connect to WebSocket on mount
  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  const isLoadingServices = isConnecting && services.length === 0
  const isLoadingMetrics = isConnecting && systemMetrics === null

  const handleAnalyze = async () => {
    await analyzeImage()
  }

  const handleReset = () => {
    reset()
  }

  const isAnalyzing = status === 'analyzing'

  return (
    <div className="min-h-screen bg-[var(--color-void-black)] relative overflow-hidden">
      {/* Tactical Grid Background */}
      <TacticalGrid />

      {/* Header */}
      <motion.header
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="relative z-10 bg-[var(--color-shadow-black)]/95 backdrop-blur-sm border-b border-[var(--color-steel)]"
        style={{
          boxShadow: 'var(--shadow-subtle)'
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <motion.div
              initial={{ x: -30, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.1, duration: 0.5 }}
            >
              <div className="flex items-center gap-4">
                <div className="relative">
                  <ShieldCheckIcon className="w-10 h-10 text-[var(--color-tactical-red)]" />
                </div>
                <div>
                  <h1 className="text-3xl font-['Rajdhani'] font-bold text-[var(--color-white)] tracking-wide">
                    ND Ninja Server
                  </h1>
                  <p className="text-[var(--color-muted-gray)] mt-0.5 font-['Inter'] text-sm">
                    Tactical Operations Platform
                  </p>
                </div>
              </div>
            </motion.div>
            <motion.div
              initial={{ x: 30, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              className="flex items-center gap-3 px-5 py-2.5 bg-[var(--color-charcoal)] border border-[var(--color-steel)] rounded-md"
              style={{
                boxShadow: 'var(--shadow-subtle)'
              }}
            >
              <div className="flex items-center gap-2.5">
                <div className="w-2 h-2 bg-[var(--color-online)] rounded-full"
                  style={{ animation: 'tacticalPulse 2s ease-in-out infinite' }}
                />
                <span className="text-xs font-['JetBrains_Mono'] font-medium text-[var(--color-ghost-gray)] tracking-wide uppercase">
                  Systems Online
                </span>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.header>

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
        {/* System Status Dashboard */}
        <motion.section
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          <StatusDashboard
            metrics={systemMetrics}
            isLoading={isLoadingMetrics}
          />
        </motion.section>

        {/* Prompt Reverser Section */}
        <motion.section
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2.5 bg-[var(--color-charcoal)] rounded-lg border border-[var(--color-steel)]">
                <SparklesIcon className="w-6 h-6 text-[var(--color-tactical-red)]" />
              </div>
              <div>
                <h2 className="text-2xl font-['Rajdhani'] font-bold text-[var(--color-white)] tracking-wide">
                  Prompt Reverser
                </h2>
                <div className="h-[1px] w-24 bg-[var(--color-tactical-red)] mt-1 opacity-40" />
              </div>
            </div>
            <p className="text-[var(--color-light-gray)] font-['Inter'] text-sm">
              Upload an image to analyze and extract the prompt that could generate similar results
            </p>
          </div>

          <div className="bg-[var(--color-shadow-black)] rounded-lg border border-[var(--color-steel)] p-6 relative overflow-hidden"
            style={{
              boxShadow: 'var(--shadow-elevated)'
            }}
          >
            {/* Minimal corner accents */}
            <div className="absolute top-0 left-0 w-10 h-10 border-l border-t border-[var(--color-tactical-red)] opacity-20 rounded-tl-lg" />
            <div className="absolute bottom-0 right-0 w-10 h-10 border-r border-b border-[var(--color-tactical-red)] opacity-20 rounded-br-lg" />

            <div className="relative z-10">
              {!result ? (
                <div className="space-y-6">
                  <ImageUpload
                    onImageSelect={setSelectedFile}
                    onImageRemove={() => setSelectedFile(null)}
                    selectedFile={selectedFile}
                    disabled={isAnalyzing}
                  />

                  {selectedFile && (
                    <>
                      <PlatformSelector
                        selectedPlatform={selectedPlatform}
                        onPlatformChange={setSelectedPlatform}
                        disabled={isAnalyzing}
                      />

                      <div className="flex justify-center">
                        <motion.button
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={handleAnalyze}
                          disabled={isAnalyzing}
                          className="relative group px-8 py-4 bg-gradient-to-br from-[var(--color-tactical-red)] to-[var(--color-target-red)] text-[var(--color-white)] font-['Rajdhani'] font-bold text-lg tracking-wide rounded-lg disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden transition-all"
                          style={{
                            boxShadow: isAnalyzing ? 'none' : 'var(--shadow-elevated), 0 0 20px rgba(153, 27, 27, 0.3)'
                          }}
                        >
                          {/* Tactical corner accents */}
                          <div className="absolute top-0 left-0 w-3 h-3 border-l-2 border-t-2 border-[var(--color-white)] opacity-30" />
                          <div className="absolute bottom-0 right-0 w-3 h-3 border-r-2 border-b-2 border-[var(--color-white)] opacity-30" />

                          {/* Animated background shimmer */}
                          {!isAnalyzing && (
                            <motion.div
                              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                              initial={{ x: '-100%' }}
                              animate={{ x: '200%' }}
                              transition={{ repeat: Infinity, duration: 3, ease: 'linear' }}
                            />
                          )}

                          <span className="relative z-10 flex items-center gap-2">
                            {isAnalyzing ? (
                              <>
                                <div className="w-5 h-5 border-2 border-[var(--color-white)] border-t-transparent rounded-full animate-spin" />
                                Analyzing...
                              </>
                            ) : (
                              <>
                                <SparklesIcon className="w-6 h-6" />
                                Analyze Image
                              </>
                            )}
                          </span>
                        </motion.button>
                      </div>
                    </>
                  )}

                  <AnalysisStatus
                    status={status}
                    error={error}
                    progress={progress}
                  />
                </div>
              ) : (
                <div className="space-y-6">
                  <ResultsDisplay result={result} />

                  <div className="flex justify-center pt-6 border-t border-[var(--color-steel)]">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleReset}
                      className="px-6 py-2.5 bg-[var(--color-charcoal)] border border-[var(--color-steel)] text-[var(--color-ghost-gray)] font-['Inter'] font-medium rounded-md hover:border-[var(--color-tactical-red)] hover:text-[var(--color-white)] transition-all"
                    >
                      Analyze Another Image
                    </motion.button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.section>

        {/* Services Grid Section */}
        <motion.section
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
        >
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2.5 bg-[var(--color-charcoal)] rounded-lg border border-[var(--color-steel)]">
                <ServerStackIcon className="w-6 h-6 text-[var(--color-tactical-red)]" />
              </div>
              <div>
                <h2 className="text-2xl font-['Rajdhani'] font-bold text-[var(--color-white)] tracking-wide">
                  Available Services
                </h2>
                <div className="h-[1px] w-24 bg-[var(--color-tactical-red)] mt-1 opacity-40" />
              </div>
            </div>
            <p className="text-[var(--color-light-gray)] font-['Inter'] text-sm">
              Quick access to all running services and applications
            </p>
          </div>

          {isLoadingServices ? (
            <div className="flex items-center justify-center py-16">
              <div className="relative">
                <div className="animate-spin rounded-full h-12 w-12 border-2 border-[var(--color-steel)] border-t-[var(--color-tactical-red)]" />
              </div>
            </div>
          ) : (
            <ServiceGrid services={services} />
          )}
        </motion.section>
      </main>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.5 }}
        className="relative z-10 bg-[var(--color-shadow-black)]/95 backdrop-blur-sm border-t border-[var(--color-steel)] mt-16"
        style={{
          boxShadow: 'var(--shadow-subtle)'
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-center gap-2">
            <div className="w-1 h-1 bg-[var(--color-tactical-red)] rounded-full opacity-60" />
            <p className="text-center text-xs text-[var(--color-muted-gray)] font-['JetBrains_Mono'] uppercase tracking-wide">
              ND Ninja Server • Built with Next.js, FastAPI & Docker
            </p>
            <div className="w-1 h-1 bg-[var(--color-tactical-red)] rounded-full opacity-60" />
          </div>
        </div>
      </motion.footer>
    </div>
  )
}
