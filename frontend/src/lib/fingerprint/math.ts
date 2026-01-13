/**
 * Math fingerprinting — различия в реализации Math между браузерами.
 */

export function getMathFingerprint(): string {
  try {
    const values = [
      Math.acos(0.123456789),
      Math.acosh(1e10),
      Math.asin(0.123456789),
      Math.asinh(1),
      Math.atan(2),
      Math.atanh(0.5),
      Math.cbrt(100),
      Math.cos(21 * Math.LN2),
      Math.cosh(492),
      Math.exp(1),
      Math.expm1(1),
      Math.log(Math.E),
      Math.log10(7),
      Math.log1p(Math.E - 1),
      Math.log2(Math.E),
      Math.pow(Math.PI, -100),
      Math.sin(Math.PI / 4),
      Math.sinh(Math.PI),
      Math.sqrt(2),
      Math.tan(Math.PI / 4),
      Math.tanh(Math.PI),
    ];
    
    let hash = 0;
    for (const v of values) {
      hash = ((hash << 5) - hash) + Math.floor(v * 1e10);
      hash = hash & hash;
    }
    return Math.abs(hash).toString(36);
  } catch {
    return '';
  }
}
