import { describe, expect, it } from 'vitest';

import { chunkEntityIds } from './NotesContext';

describe('chunkEntityIds', () => {
  it('splits large entity lists into backend-safe batches', () => {
    const ids = Array.from({ length: 205 }, (_, index) => `student-${index + 1}`);

    expect(chunkEntityIds(ids)).toEqual([
      ids.slice(0, 100),
      ids.slice(100, 200),
      ids.slice(200),
    ]);
  });

  it('keeps small lists unchanged', () => {
    const ids = ['student-1', 'student-2'];

    expect(chunkEntityIds(ids)).toEqual([ids]);
  });
});
