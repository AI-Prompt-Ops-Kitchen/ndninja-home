'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  CommandLineIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  BoltIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline'

export default function QuickActionsPanel() {
  const [isExpanded, setIsExpanded] = useState(false)

  const actions = [
    {
      icon: ArrowPathIcon,
      label: 'Refresh',
      action: () => window.location.reload()
    },
    {
      icon: CommandLineIcon,
      label: 'Logs',
      action: () => console.log('View logs')
    },
    {
      icon: DocumentTextIcon,
      label: 'Docs',
      action: () => window.open('/docs', '_blank')
    },
    {
      icon: BoltIcon,
      label: 'Actions',
      action: () => console.log('Quick actions')
    }
  ]

  return (
    <div className="fixed right-0 top-1/2 -translate-y-1/2 z-50">
      <motion.div
        initial={{ x: 200 }}
        animate={{ x: isExpanded ? 0 : 150 }}
        transition={{ type: 'tween', duration: 0.3, ease: 'easeInOut' }}
        className="relative"
      >
        {/* Toggle Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="absolute -left-10 top-1/2 -translate-y-1/2 w-10 h-20 bg-[var(--color-shadow-black)] border border-[var(--color-steel)] rounded-l-lg flex items-center justify-center hover:border-[var(--color-tactical-red)] transition-colors group"
          style={{
            boxShadow: 'var(--shadow-subtle)'
          }}
        >
          <motion.div
            animate={{ rotate: isExpanded ? 0 : 0 }}
            transition={{ duration: 0.2 }}
          >
            {isExpanded ? (
              <ChevronRightIcon className="w-5 h-5 text-[var(--color-light-gray)] group-hover:text-[var(--color-tactical-red)]" />
            ) : (
              <ChevronLeftIcon className="w-5 h-5 text-[var(--color-light-gray)] group-hover:text-[var(--color-tactical-red)]" />
            )}
          </motion.div>
        </button>

        {/* Actions Panel */}
        <div className="bg-[var(--color-shadow-black)]/95 backdrop-blur-sm border border-[var(--color-steel)] rounded-l-xl p-4 w-56"
          style={{
            boxShadow: 'var(--shadow-elevated)'
          }}
        >
          <div className="mb-4 pb-3 border-b border-[var(--color-steel)]">
            <h3 className="text-[var(--color-white)] font-['Rajdhani'] font-semibold text-sm tracking-wider uppercase">
              Quick Actions
            </h3>
          </div>

          <div className="space-y-2">
            {actions.map((action, index) => (
              <motion.button
                key={action.label}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: isExpanded ? 1 : 0, x: isExpanded ? 0 : 20 }}
                transition={{ delay: index * 0.05, duration: 0.2 }}
                onClick={action.action}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-md bg-[var(--color-charcoal)] border border-transparent hover:border-[var(--color-tactical-red)] transition-all group"
              >
                <div className="w-7 h-7 rounded flex items-center justify-center bg-[var(--color-steel)] group-hover:bg-[var(--color-tactical-red)]/20 transition-colors">
                  <action.icon className="w-4 h-4 text-[var(--color-light-gray)] group-hover:text-[var(--color-tactical-red)]" />
                </div>

                <span className="text-[var(--color-ghost-gray)] font-['Inter'] text-sm font-medium group-hover:text-[var(--color-white)] transition-colors">
                  {action.label}
                </span>

                <div className="ml-auto w-1 h-1 rounded-full bg-[var(--color-slate)] group-hover:bg-[var(--color-tactical-red)] transition-colors" />
              </motion.button>
            ))}
          </div>

          {/* Status Indicator */}
          <div className="mt-4 pt-3 border-t border-[var(--color-steel)] flex items-center justify-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-online)]"
              style={{ animation: 'tacticalPulse 2s ease-in-out infinite' }}
            />
            <span className="text-xs text-[var(--color-muted-gray)] font-['JetBrains_Mono'] uppercase tracking-wide">
              System Online
            </span>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
