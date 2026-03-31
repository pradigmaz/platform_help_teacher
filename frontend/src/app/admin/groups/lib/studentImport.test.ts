import { describe, expect, it } from 'vitest';

import {
  normalizeStudentImportName,
  parseStudentImportNames,
  parseStudentImports,
} from './studentImport';

describe('studentImport helpers', () => {
  it('normalizes numbered lines with punctuation noise', () => {
    expect(normalizeStudentImportName('1. Иванов Иван Иванович!!!')).toBe('Иванов Иван Иванович');
  });

  it('rejects lines without at least two name parts', () => {
    expect(normalizeStudentImportName('Иванов')).toBeNull();
  });

  it('parses only valid names from pasted text', () => {
    expect(
      parseStudentImportNames('1. Иванов Иван Иванович\n12345\n2) Петров Пётр Петрович')
    ).toEqual(['Иванов Иван Иванович', 'Петров Пётр Петрович']);
  });

  it('maps parsed names to student import payloads', () => {
    expect(parseStudentImports('1. Сидорова Анна Сергеевна')).toEqual([
      { full_name: 'Сидорова Анна Сергеевна' },
    ]);
  });
});
