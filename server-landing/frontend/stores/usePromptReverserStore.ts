import { create } from 'zustand'
import { Platform, AnalysisResult } from '@/lib/types'
import { apiClient } from '@/lib/api'

interface PromptReverserState {
  // UI State
  selectedFile: File | null
  selectedPlatform: Platform
  status: 'idle' | 'analyzing' | 'success' | 'error'
  error: string | null
  result: AnalysisResult | null
  progress: number

  // Actions
  setSelectedFile: (file: File | null) => void
  setSelectedPlatform: (platform: Platform) => void
  analyzeImage: () => Promise<void>
  reset: () => void
}

export const usePromptReverserStore = create<PromptReverserState>((set, get) => ({
  // Initial state
  selectedFile: null,
  selectedPlatform: 'midjourney',
  status: 'idle',
  error: null,
  result: null,
  progress: 0,

  // Actions
  setSelectedFile: (file) => set({ selectedFile: file }),

  setSelectedPlatform: (platform) => set({ selectedPlatform: platform }),

  analyzeImage: async () => {
    const { selectedFile, selectedPlatform } = get()

    if (!selectedFile) {
      set({ error: 'No file selected', status: 'error' })
      return
    }

    set({ status: 'analyzing', error: null, result: null, progress: 0 })

    try {
      // Simulate progress (since API doesn't provide real-time progress)
      const progressInterval = setInterval(() => {
        set((state) => ({
          progress: Math.min(state.progress + 10, 90)
        }))
      }, 500)

      const result = await apiClient.analyzeImage(
        selectedFile,
        selectedPlatform
      )

      clearInterval(progressInterval)

      set({
        status: 'success',
        result,
        error: null,
        progress: 100
      })
    } catch (err) {
      set({
        status: 'error',
        error: err instanceof Error ? err.message : 'Analysis failed',
        result: null,
        progress: 0
      })
    }
  },

  reset: () => set({
    selectedFile: null,
    selectedPlatform: 'midjourney',
    status: 'idle',
    error: null,
    result: null,
    progress: 0
  }),
}))
