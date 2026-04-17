export function formatScoreValue(value: number, fractionDigits = 1): string {
  const rounded = Number(value.toFixed(fractionDigits));
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(fractionDigits);
}
