import type { StudentImport } from '@/lib/api';

export function normalizeStudentImportName(line: string): string | null {
  const cleaned = line.replace(/^\d+[\.\)\s]+/, '').trim();
  const normalized = cleaned
    .replace(/[^\p{L}\s-]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  if (!normalized || normalized.split(' ').length < 2) {
    return null;
  }

  return normalized;
}

export function parseStudentImportNames(text: string): string[] {
  return text
    .split('\n')
    .map((line) => normalizeStudentImportName(line.trim()))
    .filter((name): name is string => Boolean(name));
}

export function parseStudentImports(text: string): StudentImport[] {
  return parseStudentImportNames(text).map((full_name) => ({ full_name }));
}
