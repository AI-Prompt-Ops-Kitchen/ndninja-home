'use client'

import { useEffect, useRef } from 'react'

export default function TacticalGrid() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    const gridSize = 60

    const drawGrid = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Subtle grid lines
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)'
      ctx.lineWidth = 1

      // Vertical lines
      for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, canvas.height)
        ctx.stroke()
      }

      // Horizontal lines
      for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(canvas.width, y)
        ctx.stroke()
      }

      // Subtle tactical accent line (very minimal)
      const time = Date.now() / 5000
      const accentOpacity = Math.sin(time) * 0.02 + 0.02
      ctx.strokeStyle = `rgba(153, 27, 27, ${accentOpacity})`
      ctx.lineWidth = 1

      // Slow moving horizontal line
      const accentY = ((Date.now() / 100) % canvas.height)
      ctx.beginPath()
      ctx.moveTo(0, accentY)
      ctx.lineTo(canvas.width, accentY)
      ctx.stroke()
    }

    const animate = () => {
      drawGrid()
      requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none opacity-60"
      style={{ zIndex: 0 }}
    />
  )
}
