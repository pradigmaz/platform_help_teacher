import { beforeEach, describe, expect, it, vi } from 'vitest';
import { clearSingleFlight } from '../single-flight';

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock('./client', () => ({
  api: {
    get: mocks.get,
  },
}));

import { GroupsAPI } from './groups';

describe('GroupsAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearSingleFlight();
  });

  it('passes include_students=false for lightweight group fetches', async () => {
    mocks.get.mockResolvedValue({ data: { id: 'group-1', students: [] } });

    await GroupsAPI.get('group-1', { includeStudents: false });

    expect(mocks.get).toHaveBeenCalledWith('/groups/group-1', {
      params: {
        include_students: false,
      },
    });
  });

  it('deduplicates identical in-flight group requests per option set', async () => {
    let resolveRequest: ((value: unknown) => void) | undefined;
    mocks.get.mockReturnValue(new Promise((resolve) => {
      resolveRequest = resolve;
    }));

    const firstRequest = GroupsAPI.get('group-1', { includeStudents: false });
    const secondRequest = GroupsAPI.get('group-1', { includeStudents: false });

    expect(mocks.get).toHaveBeenCalledTimes(1);

    resolveRequest?.({ data: { id: 'group-1', students: [] } });
    await Promise.all([firstRequest, secondRequest]);
  });
});
