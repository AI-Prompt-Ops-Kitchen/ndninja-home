// PromptKit Design Tokens
// Dark mode primary, blue/purple accents, cyberpunk-lite aesthetic

export const colors = {
  // Base
  background: '#0a0a0f',
  surface: '#111119',
  surfaceHover: '#16161f',
  elevated: '#1a1a27',
  overlay: 'rgba(10, 10, 15, 0.8)',

  // Borders
  border: '#1e1e2e',
  borderHover: '#2d2d40',
  borderActive: '#6366f1',

  // Text
  textPrimary: '#eeeef2',
  textSecondary: '#b0b0c4',
  textMuted: '#5a5a78',
  textDisabled: '#3d3d55',

  // Accent - Blue/Purple gradient
  accent: '#6366f1',
  accentHover: '#818cf8',
  accentLight: '#a5b4fc',
  accentDark: '#4f46e5',
  accentGlow: 'rgba(99, 102, 241, 0.15)',
  accentGlowStrong: 'rgba(99, 102, 241, 0.3)',

  // Purple accent
  purple: '#a855f7',
  purpleLight: '#c084fc',
  purpleDark: '#7c3aed',
  purpleGlow: 'rgba(168, 85, 247, 0.15)',

  // Cyan accent
  cyan: '#06b6d4',
  cyanLight: '#22d3ee',
  cyanGlow: 'rgba(6, 182, 212, 0.15)',

  // Semantic
  success: '#22c55e',
  successBg: 'rgba(34, 197, 94, 0.1)',
  warning: '#f59e0b',
  warningBg: 'rgba(245, 158, 11, 0.1)',
  error: '#ef4444',
  errorBg: 'rgba(239, 68, 68, 0.1)',
  info: '#3b82f6',
  infoBg: 'rgba(59, 130, 246, 0.1)',

  // Gradients (CSS strings)
  gradientPrimary: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
  gradientHero: 'linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #06b6d4 100%)',
  gradientText: 'linear-gradient(90deg, #818cf8 0%, #c084fc 50%, #22d3ee 100%)',
  gradientGlow: 'radial-gradient(600px circle, rgba(99, 102, 241, 0.08), transparent 70%)',
  gradientMesh: 'radial-gradient(at 27% 37%, rgba(99, 102, 241, 0.12) 0px, transparent 50%), radial-gradient(at 97% 21%, rgba(168, 85, 247, 0.08) 0px, transparent 50%), radial-gradient(at 52% 99%, rgba(6, 182, 212, 0.06) 0px, transparent 50%)',
} as const;

export const typography = {
  fontFamily: {
    sans: 'var(--font-inter), system-ui, -apple-system, sans-serif',
    mono: 'JetBrains Mono, Fira Code, monospace',
  },
  fontSize: {
    xs: ['0.75rem', { lineHeight: '1rem' }],
    sm: ['0.875rem', { lineHeight: '1.25rem' }],
    base: ['1rem', { lineHeight: '1.5rem' }],
    lg: ['1.125rem', { lineHeight: '1.75rem' }],
    xl: ['1.25rem', { lineHeight: '1.75rem' }],
    '2xl': ['1.5rem', { lineHeight: '2rem' }],
    '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
    '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
    '5xl': ['3rem', { lineHeight: '1.1' }],
    '6xl': ['3.75rem', { lineHeight: '1.05' }],
    '7xl': ['4.5rem', { lineHeight: '1' }],
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },
} as const;

export const spacing = {
  px: '1px',
  0: '0',
  0.5: '0.125rem',
  1: '0.25rem',
  1.5: '0.375rem',
  2: '0.5rem',
  2.5: '0.625rem',
  3: '0.75rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  8: '2rem',
  10: '2.5rem',
  12: '3rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
} as const;

export const borderRadius = {
  none: '0',
  sm: '0.375rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1rem',
  '2xl': '1.25rem',
  '3xl': '1.5rem',
  full: '9999px',
} as const;

export const shadows = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.2)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -4px rgba(0, 0, 0, 0.2)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.2)',
  glow: '0 0 20px rgba(99, 102, 241, 0.15), 0 0 60px rgba(99, 102, 241, 0.05)',
  glowStrong: '0 0 30px rgba(99, 102, 241, 0.25), 0 0 80px rgba(99, 102, 241, 0.1)',
  glowPurple: '0 0 20px rgba(168, 85, 247, 0.15), 0 0 60px rgba(168, 85, 247, 0.05)',
  inner: 'inset 0 2px 4px rgba(0, 0, 0, 0.2)',
  card: '0 4px 20px rgba(0, 0, 0, 0.25)',
  cardHover: '0 8px 30px rgba(0, 0, 0, 0.3), 0 0 20px rgba(99, 102, 241, 0.08)',
} as const;

// Framer Motion animation presets
export const animations = {
  // Page transitions
  pageEnter: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
    transition: { duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] },
  },

  // Fade in up (for scroll reveals)
  fadeInUp: {
    initial: { opacity: 0, y: 30 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, margin: '-50px' },
    transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] },
  },

  // Fade in (simple)
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.4 },
  },

  // Scale up (for cards, buttons)
  scaleUp: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    transition: { duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] },
  },

  // Stagger children
  stagger: {
    animate: { transition: { staggerChildren: 0.08 } },
  },

  // Stagger item
  staggerItem: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.4 } },
  },

  // Hover lift
  hoverLift: {
    whileHover: { y: -4, transition: { duration: 0.2 } },
    whileTap: { scale: 0.98 },
  },

  // Pulse glow
  pulseGlow: {
    animate: {
      boxShadow: [
        '0 0 20px rgba(99, 102, 241, 0.1)',
        '0 0 40px rgba(99, 102, 241, 0.2)',
        '0 0 20px rgba(99, 102, 241, 0.1)',
      ],
    },
    transition: { duration: 2, repeat: Infinity, ease: 'easeInOut' },
  },

  // Slide in from left
  slideInLeft: {
    initial: { opacity: 0, x: -30 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
  },

  // Slide in from right
  slideInRight: {
    initial: { opacity: 0, x: 30 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
  },

  // Spring bounce
  spring: {
    type: 'spring' as const,
    stiffness: 300,
    damping: 20,
  },

  // Smooth ease
  smooth: {
    duration: 0.3,
    ease: [0.25, 0.46, 0.45, 0.94],
  },
} as const;

// Z-index scale
export const zIndex = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  overlay: 30,
  modal: 40,
  popover: 50,
  toast: 60,
  tooltip: 70,
} as const;
