import { beforeEach, describe, expect, it, vi } from 'vitest';
import { clearSingleFlight } from '../single-flight';

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
  apiPut: vi.fn(),
  publicGet: vi.fn(),
  publicPost: vi.fn(),
}));

vi.mock('./client', () => ({
  api: {
    get: mocks.apiGet,
    post: mocks.apiPost,
    delete: mocks.apiDelete,
    put: mocks.apiPut,
  },
  publicApi: {
    get: mocks.publicGet,
    post: mocks.publicPost,
  },
}));

import { ReportsAPI, PublicReportAPI } from './reports';

describe('ReportsAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearSingleFlight();
  });

  it('passes server-side filters when listing reports', async () => {
    mocks.apiGet.mockResolvedValue({ data: { reports: [], total: 0 } });

    await ReportsAPI.list({ groupId: 'group-1', includeInactive: true });

    expect(mocks.apiGet).toHaveBeenCalledWith('/admin/reports', {
      params: {
        group_id: 'group-1',
        include_inactive: true,
      },
    });
  });

  it('deduplicates identical in-flight list requests', async () => {
    let resolveRequest: ((value: unknown) => void) | undefined;
    mocks.apiGet.mockReturnValue(new Promise((resolve) => {
      resolveRequest = resolve;
    }));

    const firstRequest = ReportsAPI.list({ groupId: 'group-1' });
    const secondRequest = ReportsAPI.list({ groupId: 'group-1' });

    expect(mocks.apiGet).toHaveBeenCalledTimes(1);

    resolveRequest?.({ data: { reports: [], total: 0 } });
    await Promise.all([firstRequest, secondRequest]);
  });
});

describe('PublicReportAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('passes abort signal to the public report request', async () => {
    const controller = new AbortController();
    mocks.publicGet.mockResolvedValue({ data: { students: [] } });

    await PublicReportAPI.getReport('CODE1234', 'second', controller.signal);

    expect(mocks.publicGet).toHaveBeenCalledWith(
      '/public/report/CODE1234?attestation=second',
      { signal: controller.signal },
    );
  });
});
