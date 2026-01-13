/**
 * Audio fingerprinting.
 */
import type { AudioContextInfo } from './types';

export function getAudioFingerprint(): { hash?: string; context?: AudioContextInfo } {
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioCtx) return {};
    
    const ctx = new AudioCtx();
    const contextInfo: AudioContextInfo = {
      sampleRate: ctx.sampleRate,
      maxChannelCount: ctx.destination.maxChannelCount,
      state: ctx.state,
    };
    
    const oscillator = ctx.createOscillator();
    const analyser = ctx.createAnalyser();
    const gain = ctx.createGain();
    const compressor = ctx.createDynamicsCompressor();
    
    gain.gain.value = 0;
    oscillator.type = 'triangle';
    oscillator.frequency.value = 10000;
    
    compressor.threshold.value = -50;
    compressor.knee.value = 40;
    compressor.ratio.value = 12;
    compressor.attack.value = 0;
    compressor.release.value = 0.25;
    
    oscillator.connect(compressor);
    compressor.connect(analyser);
    analyser.connect(gain);
    gain.connect(ctx.destination);
    
    oscillator.start(0);
    
    const bins = new Float32Array(analyser.frequencyBinCount);
    analyser.getFloatFrequencyData(bins);
    
    oscillator.stop();
    ctx.close();
    
    let hash = 0;
    for (let i = 0; i < bins.length; i++) {
      hash = ((hash << 5) - hash) + Math.floor(bins[i] * 1000);
      hash = hash & hash;
    }
    
    return {
      hash: Math.abs(hash).toString(36),
      context: contextInfo,
    };
  } catch {
    return {};
  }
}
