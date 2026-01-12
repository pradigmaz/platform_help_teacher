import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format group code: ИС1231ОТ -> ИС1-231-ОТ
 * Pattern: 2-3 letters + 1 digit + 3 digits + 2 letters (suffix)
 */
export function formatGroupCode(code: string): string {
  const match = code.match(/^([А-ЯA-Z]{2,3})(\d)(\d{3})([А-ЯA-Z]{2})$/i);
  if (match) {
    return `${match[1]}${match[2]}-${match[3]}-${match[4]}`;
  }
  return code;
}
