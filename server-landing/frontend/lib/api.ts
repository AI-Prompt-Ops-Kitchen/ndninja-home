import type {
  PlatformInfo,
  AnalysisResult,
  AsyncAnalysisResponse,
  JobStatus,
  ServiceInfo,
  SystemMetrics,
  HealthStatus,
  Platform,
} from './types'

// Transform API response to frontend format
function transformAnalysisResponse(apiResponse: any, platform: Platform): AnalysisResult {
  return {
    main_prompt: apiResponse.prompt?.main || '',
    variations: (apiResponse.prompt?.variations || []).map((v: string, i: number) => ({
      prompt: v,
      confidence: apiResponse.confidence?.content || 0.5
    })),
    negative_prompt: apiResponse.prompt?.negative || '',
    style_analysis: apiResponse.style ? [{
      style: apiResponse.style.art_style || 'unknown',
      confidence: apiResponse.confidence?.style || 0.5
    }] : [],
    composition_analysis: {
      aspect: apiResponse.composition?.type || 'unknown',
      elements: apiResponse.composition?.color_palette || [],
      composition_type: apiResponse.composition?.perspective || 'unknown'
    },
    platform,
    confidence_score: apiResponse.confidence?.overall || 0.5,
    processing_time: (apiResponse.processing_time_ms || 0) / 1000  // Convert ms to seconds
  }
}

class ApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = typeof window !== 'undefined'
      ? window.location.origin
      : 'http://100.77.248.9:80'
  }

  private async fetchJson<T>(
    url: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Prompt Reverser API methods

  async getPlatforms(): Promise<PlatformInfo[]> {
    return this.fetchJson<PlatformInfo[]>(`${this.baseUrl}/api/prompt-reverser/platforms`)
  }

  async analyzeImage(
    file: File,
    platform: Platform,
    options?: Record<string, any>
  ): Promise<AnalysisResult> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('platform', platform)
    if (options) {
      formData.append('options', JSON.stringify(options))
    }

    const response = await fetch(`${this.baseUrl}/api/prompt-reverser/analyze`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      // Handle both array and string detail formats
      const errorMessage = Array.isArray(error.detail)
        ? error.detail[0]?.msg || 'Validation error'
        : (error.detail || `HTTP ${response.status}`)
      throw new Error(errorMessage)
    }

    const apiResponse = await response.json()
    return transformAnalysisResponse(apiResponse, platform)
  }

  async analyzeImageAsync(
    file: File,
    platform: Platform,
    options?: Record<string, any>
  ): Promise<AsyncAnalysisResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('platform', platform)
    if (options) {
      formData.append('options', JSON.stringify(options))
    }

    const response = await fetch(`${this.baseUrl}/api/prompt-reverser/analyze/async`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      // Handle both array and string detail formats
      const errorMessage = Array.isArray(error.detail)
        ? error.detail[0]?.msg || 'Validation error'
        : (error.detail || `HTTP ${response.status}`)
      throw new Error(errorMessage)
    }

    return response.json()
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.fetchJson<JobStatus>(`${this.baseUrl}/api/prompt-reverser/analyze/${jobId}`)
  }

  // Landing Backend API methods

  async getHealth(): Promise<HealthStatus> {
    return this.fetchJson<HealthStatus>(`${this.baseUrl}/api/health`)
  }

  async getServices(): Promise<ServiceInfo[]> {
    return this.fetchJson<ServiceInfo[]>(`${this.baseUrl}/api/services`)
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    return this.fetchJson<SystemMetrics>(`${this.baseUrl}/api/system`)
  }
}

// Singleton instance
export const apiClient = new ApiClient()
