import { describe, expect, it } from 'vitest';
import fc from 'fast-check';
import {
  normalizeStudentImportName,
  parseStudentImportNames,
  parseStudentImports,
} from './studentImport';

const wordArb = fc.constantFrom('Иванов', 'Петров', 'Сидоров', 'Анна', 'Мария', 'Алексей', 'Smoke');
const validNameArb = fc
  .array(wordArb, { minLength: 2, maxLength: 4 })
  .map((words) => words.join(' '));

describe('studentImport property tests', () => {
  it('normalizes numbered lines into stable multi-word names', () => {
    fc.assert(
      fc.property(fc.integer({ min: 1, max: 999 }), validNameArb, (index, name) => {
        const normalized = normalizeStudentImportName(`${index}. ${name}`);
        expect(normalized).toBe(name);
      })
    );
  });

  it('keeps parseStudentImports aligned with parseStudentImportNames', () => {
    fc.assert(
      fc.property(fc.array(validNameArb, { minLength: 1, maxLength: 8 }), (names) => {
        const text = names.map((name, index) => `${index + 1}) ${name}`).join('\n');
        expect(parseStudentImports(text).map((item) => item.full_name)).toEqual(parseStudentImportNames(text));
      })
    );
  });
});
