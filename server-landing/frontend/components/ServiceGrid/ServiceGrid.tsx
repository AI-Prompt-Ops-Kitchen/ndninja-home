'use client'

import { ServiceInfo } from '@/lib/types'
import ServiceCard from './ServiceCard'

interface ServiceGridProps {
  services: ServiceInfo[]
}

export default function ServiceGrid({ services }: ServiceGridProps) {
  if (services.length === 0) {
    return (
      <div className="text-center py-12 bg-[var(--color-shadow-black)] rounded-xl border border-[var(--color-steel)] p-8"
        style={{ boxShadow: 'var(--shadow-subtle)' }}
      >
        <p className="text-[var(--color-muted-gray)] font-['Inter']">Services loading...</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {services.map((service, index) => (
        <ServiceCard key={`${service.name}-${index}`} service={service} index={index} />
      ))}
    </div>
  )
}
