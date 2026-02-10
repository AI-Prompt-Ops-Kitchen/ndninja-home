// Prompt Reverser API Types

export type Platform = 'midjourney' | 'dalle3' | 'flux' | 'nanobanana'

export interface PlatformInfo {
  name: string
  value: Platform
  description: string
  options?: Record<string, any>
}

export interface AnalysisRequest {
  file: File
  platform: Platform
  options?: Record<string, any>
}

export interface PromptVariation {
  prompt: string
  confidence: number
}

export interface StyleAnalysis {
  style: string
  confidence: number
}

export interface CompositionAnalysis {
  aspect: string
  elements: string[]
  composition_type: string
}

export interface AnalysisResult {
  main_prompt: string
  variations: PromptVariation[]
  negative_prompt?: string
  style_analysis: StyleAnalysis[]
  composition_analysis: CompositionAnalysis
  platform: Platform
  confidence_score: number
  processing_time: number
}

export interface AsyncAnalysisResponse {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  result?: AnalysisResult
  error?: string
  progress?: number
}

// Service Status Types

export interface ServiceInfo {
  name: string
  url: string
  port: number
  description: string
  icon: string
  status?: 'online' | 'offline' | 'unknown'
  response_time?: number
}

export interface SystemMetrics {
  cpu_percent: number
  memory_percent: number
  disk_percent: number
  container_count: number
  uptime_seconds: number
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  uptime: number
  timestamp: string
}
