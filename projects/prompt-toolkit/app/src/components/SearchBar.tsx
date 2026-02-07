'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Command, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchBarProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSubmit?: (value: string) => void;
  className?: string;
  showShortcut?: boolean;
  autoFocus?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function SearchBar({
  placeholder = 'Search prompts...',
  value: controlledValue,
  onChange,
  onSubmit,
  className,
  showShortcut = true,
  autoFocus = false,
  size = 'md',
}: SearchBarProps) {
  const [internalValue, setInternalValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const value = controlledValue ?? internalValue;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === 'Escape') {
        inputRef.current?.blur();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleChange = (val: string) => {
    setInternalValue(val);
    onChange?.(val);
  };

  const sizeClasses = {
    sm: 'py-2 pl-9 pr-4 text-sm',
    md: 'py-2.5 pl-10 pr-4 text-sm',
    lg: 'py-3 pl-11 pr-4 text-base',
  };

  const iconSizes = {
    sm: 'h-4 w-4 left-2.5',
    md: 'h-4 w-4 left-3',
    lg: 'h-5 w-5 left-3.5',
  };

  return (
    <div className={cn('relative group', className)}>
      <Search
        className={cn(
          'absolute top-1/2 -translate-y-1/2 transition-colors',
          iconSizes[size],
          isFocused ? 'text-indigo-400' : 'text-gray-500'
        )}
      />
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        onKeyDown={(e) => e.key === 'Enter' && onSubmit?.(value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className={cn(
          'w-full rounded-xl border bg-gray-900/80 text-gray-200 placeholder:text-gray-500',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-indigo-600/50 focus:border-indigo-600/50',
          isFocused
            ? 'border-indigo-600/50 shadow-[0_0_20px_rgba(99,102,241,0.1)]'
            : 'border-gray-800 hover:border-gray-700',
          sizeClasses[size]
        )}
      />

      {/* Keyboard shortcut hint */}
      <AnimatePresence>
        {showShortcut && !isFocused && !value && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1"
          >
            <kbd className="flex items-center gap-0.5 rounded-md border border-gray-700 bg-gray-800 px-1.5 py-0.5 text-xs text-gray-500">
              <Command className="h-3 w-3" />K
            </kbd>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Clear button */}
      <AnimatePresence>
        {value && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-md text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
            onClick={() => handleChange('')}
          >
            <X className="h-3.5 w-3.5" />
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}
