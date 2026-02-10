'use client'

import { SystemMetrics } from '@/lib/types'
import { cn } from '@/lib/utils'
import {
  CpuChipIcon,
  CircleStackIcon,
  ServerIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

interface StatusDashboardProps {
  metrics: SystemMetrics | null
  isLoading?: boolean
}

interface MetricCardProps {
  icon: React.ElementType
  label: string
  value: string
  percent?: number
  colorClass?: string
}

function MetricCard({ icon: Icon, label, value, percent, colorClass = 'bg-blue-500' }: MetricCardProps) {
  return (
    <div className="bg-[var(--color-shadow-black)] rounded-lg border border-[var(--color-steel)] p-4 transition-all hover:border-[var(--color-tactical-red)]"
      style={{ boxShadow: 'var(--shadow-subtle)' }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-[var(--color-charcoal)] rounded-lg border border-[var(--color-steel)]">
            <Icon className="w-5 h-5 text-[var(--color-light-gray)]" />
          </div>
          <span className="text-sm font-['Inter'] font-medium text-[var(--color-ghost-gray)]">{label}</span>
        </div>
        <span className="text-lg font-['Rajdhani'] font-bold text-[var(--color-white)]">{value}</span>
      </div>

      {percent !== undefined && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-[var(--color-muted-gray)] font-['JetBrains_Mono']">
            <span>Usage</span>
            <span>{percent.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-[var(--color-deep-charcoal)] rounded-full h-2 overflow-hidden border border-[var(--color-steel)]">
            <div
              className={cn(
                "h-full transition-all duration-500 rounded-full",
                colorClass
              )}
              style={{ width: `${Math.min(percent, 100)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  const parts = []
  if (days > 0) parts.push(`${days}d`)
  if (hours > 0) parts.push(`${hours}h`)
  if (minutes > 0 || parts.length === 0) parts.push(`${minutes}m`)

  return parts.join(' ')
}

export default function StatusDashboard({ metrics, isLoading = false }: StatusDashboardProps) {
  if (isLoading) {
    return (
      <div className="bg-[var(--color-shadow-black)] rounded-xl border border-[var(--color-steel)] p-6"
        style={{ boxShadow: 'var(--shadow-subtle)' }}
      >
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-[var(--color-steel)] border-t-[var(--color-tactical-red)]" />
        </div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="bg-[var(--color-shadow-black)] rounded-xl border border-[var(--color-steel)] p-6"
        style={{ boxShadow: 'var(--shadow-subtle)' }}
      >
        <p className="text-center text-[var(--color-muted-gray)] font-['Inter']">System metrics loading...</p>
      </div>
    )
  }

  const getCpuColorClass = (percent: number) => {
    if (percent >= 80) return 'bg-[var(--color-target-red)]'
    if (percent >= 60) return 'bg-yellow-600'
    return 'bg-green-600'
  }

  const getMemoryColorClass = (percent: number) => {
    if (percent >= 90) return 'bg-[var(--color-target-red)]'
    if (percent >= 70) return 'bg-yellow-600'
    return 'bg-blue-600'
  }

  const getDiskColorClass = (percent: number) => {
    if (percent >= 90) return 'bg-[var(--color-target-red)]'
    if (percent >= 75) return 'bg-yellow-600'
    return 'bg-purple-600'
  }

  return (
    <div className="bg-[var(--color-shadow-black)] rounded-xl border border-[var(--color-steel)] p-6 relative overflow-hidden"
      style={{ boxShadow: 'var(--shadow-elevated)' }}
    >
      {/* Tactical corner accents */}
      <div className="absolute top-0 left-0 w-10 h-10 border-l border-t border-[var(--color-tactical-red)] opacity-20 rounded-tl-lg" />
      <div className="absolute bottom-0 right-0 w-10 h-10 border-r border-b border-[var(--color-tactical-red)] opacity-20 rounded-br-lg" />

      <h2 className="text-xl font-['Rajdhani'] font-bold text-[var(--color-white)] mb-6 flex items-center gap-2 relative z-10">
        <ServerIcon className="w-6 h-6 text-[var(--color-tactical-red)]" />
        System Status
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 relative z-10">
        <MetricCard
          icon={CpuChipIcon}
          label="CPU"
          value={`${metrics.cpu_percent.toFixed(1)}%`}
          percent={metrics.cpu_percent}
          colorClass={getCpuColorClass(metrics.cpu_percent)}
        />

        <MetricCard
          icon={CircleStackIcon}
          label="Memory"
          value={`${metrics.memory_percent.toFixed(1)}%`}
          percent={metrics.memory_percent}
          colorClass={getMemoryColorClass(metrics.memory_percent)}
        />

        <MetricCard
          icon={ServerIcon}
          label="Disk"
          value={`${metrics.disk_percent.toFixed(1)}%`}
          percent={metrics.disk_percent}
          colorClass={getDiskColorClass(metrics.disk_percent)}
        />

        <MetricCard
          icon={ClockIcon}
          label="Uptime"
          value={formatUptime(metrics.uptime_seconds)}
        />
      </div>

      <div className="mt-4 pt-4 border-t border-[var(--color-steel)] flex items-center justify-between text-sm text-[var(--color-ghost-gray)] font-['Inter'] relative z-10">
        <span>Docker Containers: <span className="font-['JetBrains_Mono'] text-[var(--color-white)]">{metrics.container_count}</span></span>
        <span className="text-xs text-[var(--color-muted-gray)] font-['JetBrains_Mono']">Live updates</span>
      </div>
    </div>
  )
}
