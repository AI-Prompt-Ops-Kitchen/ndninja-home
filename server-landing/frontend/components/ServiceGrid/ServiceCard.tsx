'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { ServiceInfo } from '@/lib/types'
import { cn } from '@/lib/utils'
import {
  ShieldCheckIcon,
  CpuChipIcon,
  DocumentTextIcon,
  VideoCameraIcon,
  SparklesIcon,
  Cog6ToothIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline'

interface ServiceCardProps {
  service: ServiceInfo
  index?: number
}

const iconMap: Record<string, any> = {
  shield: ShieldCheckIcon,
  cpu: CpuChipIcon,
  document: DocumentTextIcon,
  video: VideoCameraIcon,
  sparkles: SparklesIcon,
  workflow: Cog6ToothIcon,
}

export default function ServiceCard({ service, index = 0 }: ServiceCardProps) {
  const Icon = iconMap[service.icon] || Cog6ToothIcon
  const [isHovered, setIsHovered] = useState(false)

  const isOnline = service.status === 'online'
  const statusColor = isOnline ? 'var(--color-online)' : 'var(--color-offline)'

  return (
    <motion.a
      href={service.url}
      target="_blank"
      rel="noopener noreferrer"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4, ease: 'easeOut' }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="group relative block"
    >
      {/* Main Card */}
      <div
        className="relative bg-[var(--color-shadow-black)] border border-[var(--color-steel)] rounded-lg p-5 transition-all duration-300"
        style={{
          boxShadow: isHovered ? 'var(--shadow-elevated), inset 0 0 0 1px var(--color-tactical-red)' : 'var(--shadow-subtle)',
          borderColor: isHovered ? 'var(--color-tactical-red)' : 'var(--color-steel)'
        }}
      >
        {/* Status Indicator */}
        <div className="absolute top-4 right-4 flex items-center gap-2">
          <div
            className={cn("w-2 h-2 rounded-full transition-all duration-300")}
            style={{
              backgroundColor: statusColor,
              boxShadow: isOnline ? '0 0 8px rgba(16, 185, 129, 0.5)' : 'none'
            }}
          />
          <span className="text-xs font-['JetBrains_Mono'] font-medium tracking-wide uppercase"
            style={{ color: statusColor }}
          >
            {isOnline ? 'Online' : 'Offline'}
          </span>
        </div>

        {/* Icon */}
        <div
          className="w-14 h-14 rounded-md flex items-center justify-center mb-4 transition-all duration-300"
          style={{
            background: isHovered ? 'rgba(153, 27, 27, 0.1)' : 'var(--color-charcoal)',
            border: `1px solid ${isHovered ? 'var(--color-tactical-red)' : 'var(--color-steel)'}`,
          }}
        >
          <Icon
            className="w-7 h-7 transition-colors duration-300"
            style={{
              color: isHovered ? 'var(--color-tactical-red)' : 'var(--color-light-gray)'
            }}
          />
        </div>

        {/* Content */}
        <div className="mb-4">
          <h3 className="text-lg font-['Rajdhani'] font-semibold text-[var(--color-white)] mb-2 flex items-center gap-2 transition-colors">
            <span>{service.name}</span>
            <ArrowTopRightOnSquareIcon
              className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-all transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
              style={{ color: 'var(--color-tactical-red)' }}
            />
          </h3>
          <p className="text-sm text-[var(--color-light-gray)] leading-relaxed font-['Inter']">
            {service.description}
          </p>
        </div>

        {/* Footer with Metrics */}
        <div className="flex items-center justify-between pt-4 border-t"
          style={{ borderColor: 'var(--color-steel)' }}
        >
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--color-muted-gray)] font-['JetBrains_Mono'] uppercase">Port</span>
            <span className="text-sm font-['JetBrains_Mono'] font-semibold text-[var(--color-ghost-gray)]">
              {service.port}
            </span>
          </div>

          {service.response_time !== undefined && service.response_time !== null && (
            <div className="flex items-center gap-2">
              <div className="w-1 h-1 rounded-full bg-[var(--color-online)]" />
              <span className="text-xs text-[var(--color-online)] font-['JetBrains_Mono']">
                {service.response_time}ms
              </span>
            </div>
          )}
        </div>

        {/* Minimal corner accents */}
        <div
          className="absolute top-0 left-0 w-8 h-8 border-l border-t opacity-20 rounded-tl-lg transition-opacity duration-300"
          style={{
            borderColor: isHovered ? 'var(--color-tactical-red)' : 'var(--color-steel)',
            opacity: isHovered ? 0.4 : 0.2
          }}
        />
        <div
          className="absolute bottom-0 right-0 w-8 h-8 border-r border-b opacity-20 rounded-br-lg transition-opacity duration-300"
          style={{
            borderColor: isHovered ? 'var(--color-tactical-red)' : 'var(--color-steel)',
            opacity: isHovered ? 0.4 : 0.2
          }}
        />
      </div>
    </motion.a>
  )
}
