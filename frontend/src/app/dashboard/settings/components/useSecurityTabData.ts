'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { DevicesAPI, type Device } from '@/lib/api/devices';
import { SessionsAPI, type SessionListResponse } from '@/lib/api/sessions';
import { loadCached } from '@/lib/api/read-cache';

const SESSIONS_CACHE_KEY = 'user:sessions';
const DEVICES_CACHE_KEY = 'user:devices';
const SECURITY_CACHE_TTL_MS = 15_000;

async function getSessions(forceRefresh = false) {
  return loadCached(SESSIONS_CACHE_KEY, () => SessionsAPI.getSessions(), {
    forceRefresh,
    ttlMs: SECURITY_CACHE_TTL_MS,
  });
}

async function getDevices(forceRefresh = false) {
  return loadCached(DEVICES_CACHE_KEY, () => DevicesAPI.getDevices(), {
    forceRefresh,
    ttlMs: SECURITY_CACHE_TTL_MS,
  });
}

export function useSecurityTabData() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(false);
  const [sessionsData, setSessionsData] = useState<SessionListResponse | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [revokingSessionId, setRevokingSessionId] = useState<string | null>(null);
  const [revokingAll, setRevokingAll] = useState(false);
  const [deviceActionId, setDeviceActionId] = useState<string | null>(null);
  const hasLoadedRef = useRef(false);

  const loadSecurityData = useCallback(async (options?: { forceRefresh?: boolean }) => {
    const forceRefresh = options?.forceRefresh ?? false;
    if (!hasLoadedRef.current) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }

    setError(false);
    try {
      const [nextSessions, nextDevices] = await Promise.all([
        getSessions(forceRefresh),
        getDevices(forceRefresh),
      ]);
      setSessionsData(nextSessions);
      setDevices(nextDevices.devices);
      hasLoadedRef.current = true;
    } catch (nextError) {
      console.error('Security tab fetch failed', nextError);
      setError(true);
      toast.error('Ошибка загрузки данных безопасности');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadSecurityData();
  }, [loadSecurityData]);

  const revokeSession = useCallback(async (sessionId: string) => {
    setRevokingSessionId(sessionId);
    try {
      await SessionsAPI.revokeSession(sessionId);
      toast.success('Сессия завершена');
      await loadSecurityData({ forceRefresh: true });
    } catch {
      toast.error('Ошибка завершения сессии');
    } finally {
      setRevokingSessionId(null);
    }
  }, [loadSecurityData]);

  const revokeAllSessions = useCallback(async () => {
    setRevokingAll(true);
    try {
      const result = await SessionsAPI.revokeAllSessions();
      toast.success(result.message);
      await loadSecurityData({ forceRefresh: true });
    } catch {
      toast.error('Ошибка завершения сессий');
    } finally {
      setRevokingAll(false);
    }
  }, [loadSecurityData]);

  const confirmDevice = useCallback(async (deviceId: string) => {
    setDeviceActionId(deviceId);
    try {
      await DevicesAPI.confirmDevice(deviceId);
      toast.success('Устройство подтверждено');
      await loadSecurityData({ forceRefresh: true });
    } catch (nextError) {
      console.error('Device confirm failed', nextError);
      toast.error('Ошибка подтверждения устройства');
    } finally {
      setDeviceActionId(null);
    }
  }, [loadSecurityData]);

  const deleteDevice = useCallback(async (deviceId: string) => {
    setDeviceActionId(deviceId);
    try {
      await DevicesAPI.deleteDevice(deviceId);
      toast.success('Устройство отвязано');
      await loadSecurityData({ forceRefresh: true });
    } catch (nextError) {
      console.error('Device delete failed', nextError);
      toast.error('Ошибка отвязки устройства');
    } finally {
      setDeviceActionId(null);
    }
  }, [loadSecurityData]);

  return {
    loading,
    refreshing,
    error,
    sessionsData,
    devices,
    revokingSessionId,
    revokingAll,
    deviceActionId,
    reload: () => loadSecurityData({ forceRefresh: true }),
    revokeSession,
    revokeAllSessions,
    confirmDevice,
    deleteDevice,
  };
}
