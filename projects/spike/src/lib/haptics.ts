'use client';

// Haptic feedback — gentle, never startling
// Falls back silently on devices that don't support it

export function hapticTap() {
  try {
    navigator?.vibrate?.(8); // Very short, satisfying click
  } catch {}
}

export function hapticSuccess() {
  try {
    navigator?.vibrate?.([10, 40, 10]); // Double-tap pattern — like a tiny celebration
  } catch {}
}

export function hapticSlide() {
  try {
    navigator?.vibrate?.(4); // Barely-there tick for slider snaps
  } catch {}
}
