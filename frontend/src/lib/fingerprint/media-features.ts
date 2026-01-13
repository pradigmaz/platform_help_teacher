/**
 * CSS media features detection.
 */
import type { DeviceFingerprint } from './types';

export function getMediaFeatures(): Partial<DeviceFingerprint> {
  const result: Partial<DeviceFingerprint> = {};
  
  try {
    // Color gamut
    if (matchMedia('(color-gamut: rec2020)').matches) result.colorGamut = 'rec2020';
    else if (matchMedia('(color-gamut: p3)').matches) result.colorGamut = 'p3';
    else if (matchMedia('(color-gamut: srgb)').matches) result.colorGamut = 'srgb';
    
    // Contrast
    if (matchMedia('(prefers-contrast: more)').matches) result.contrast = 'more';
    else if (matchMedia('(prefers-contrast: less)').matches) result.contrast = 'less';
    else result.contrast = 'no-preference';
    
    // Motion
    result.reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    // Transparency
    result.reducedTransparency = matchMedia('(prefers-reduced-transparency: reduce)').matches;
    
    // Forced colors
    result.forcedColors = matchMedia('(forced-colors: active)').matches;
    
    // HDR
    result.hdr = matchMedia('(dynamic-range: high)').matches;
    
    // Inverted colors
    result.invertedColors = matchMedia('(inverted-colors: inverted)').matches;
  } catch {}
  
  return result;
}
