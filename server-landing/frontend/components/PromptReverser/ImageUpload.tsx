'use client'

import { useState, useRef, useCallback } from 'react'
import { ArrowUpTrayIcon, XMarkIcon, PhotoIcon } from '@heroicons/react/24/outline'
import { cn } from '@/lib/utils'

interface ImageUploadProps {
  onImageSelect: (file: File) => void
  onImageRemove: () => void
  selectedFile: File | null
  disabled?: boolean
}

const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']

export default function ImageUpload({
  onImageSelect,
  onImageRemove,
  selectedFile,
  disabled = false,
}: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return 'Please upload a PNG, JPG, or WebP image'
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'File size must be less than 50MB'
    }
    return null
  }

  const handleFile = useCallback(
    (file: File) => {
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        return
      }

      setError(null)
      onImageSelect(file)

      // Create preview
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    },
    [onImageSelect]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)

      const files = Array.from(e.dataTransfer.files)
      if (files.length > 0) {
        handleFile(files[0])
      }
    },
    [handleFile]
  )

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (files && files.length > 0) {
        handleFile(files[0])
      }
    },
    [handleFile]
  )

  const handleRemove = useCallback(() => {
    setPreview(null)
    setError(null)
    onImageRemove()
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [onImageRemove])

  const handleClick = useCallback(() => {
    if (!disabled && !selectedFile) {
      fileInputRef.current?.click()
    }
  }, [disabled, selectedFile])

  return (
    <div className="w-full">
      {!selectedFile ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
          className={cn(
            'relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all',
            'bg-[var(--color-shadow-black)]',
            isDragging
              ? 'border-[var(--color-tactical-red)] bg-[var(--color-charcoal)] scale-[1.02]'
              : 'border-[var(--color-steel)] hover:border-[var(--color-tactical-red)]',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          style={{
            boxShadow: isDragging ? 'var(--shadow-elevated)' : 'var(--shadow-subtle)'
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES.join(',')}
            onChange={handleFileInputChange}
            className="hidden"
            disabled={disabled}
          />

          <div className="flex flex-col items-center gap-4">
            <div className={cn(
              'p-4 rounded-full border transition-all',
              isDragging
                ? 'bg-[var(--color-tactical-red)]/20 border-[var(--color-tactical-red)]'
                : 'bg-[var(--color-charcoal)] border-[var(--color-steel)]'
            )}>
              <PhotoIcon className={cn(
                'w-12 h-12 transition-colors',
                isDragging ? 'text-[var(--color-tactical-red)]' : 'text-[var(--color-light-gray)]'
              )} />
            </div>

            <div>
              <p className="text-lg font-['Rajdhani'] font-semibold text-[var(--color-white)]">
                Drop your image here
              </p>
              <p className="text-sm font-['Inter'] text-[var(--color-muted-gray)] mt-1">
                or click to browse
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs font-['JetBrains_Mono'] text-[var(--color-muted-gray)]">
              <ArrowUpTrayIcon className="w-4 h-4" />
              <span>PNG, JPG, WebP up to 50MB</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="relative border-2 border-[var(--color-steel)] rounded-lg overflow-hidden bg-[var(--color-shadow-black)]"
          style={{ boxShadow: 'var(--shadow-elevated)' }}
        >
          <button
            onClick={handleRemove}
            disabled={disabled}
            className={cn(
              'absolute top-2 right-2 z-10 p-2 bg-[var(--color-target-red)] text-[var(--color-white)] rounded-full',
              'hover:bg-[var(--color-tactical-red)] transition-colors',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            style={{ boxShadow: 'var(--shadow-elevated)' }}
          >
            <XMarkIcon className="w-5 h-5" />
          </button>

          {preview && (
            <div className="relative w-full aspect-video bg-[var(--color-deep-charcoal)] border border-[var(--color-steel)]">
              <img
                src={preview}
                alt="Preview"
                className="w-full h-full object-contain"
              />
            </div>
          )}

          <div className="p-4 border-t border-[var(--color-steel)]">
            <p className="text-sm font-['Inter'] font-medium text-[var(--color-white)] truncate">
              {selectedFile.name}
            </p>
            <p className="text-xs font-['JetBrains_Mono'] text-[var(--color-muted-gray)] mt-1">
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-3 p-3 bg-[var(--color-target-red)]/10 border border-[var(--color-target-red)] rounded-md">
          <p className="text-sm font-['Inter'] text-[var(--color-target-red)]">{error}</p>
        </div>
      )}
    </div>
  )
}
