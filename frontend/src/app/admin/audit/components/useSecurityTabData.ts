'use client';

import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import {
  SecurityAPI,
  type SecurityStatsResponse,
  type SecurityStrikesResponse,
  type UserInfoResponse,
} from '@/lib/api';
import {
  buildSecurityUserInfoMap,
  extractSecurityUserIds,
} from './securityTabModel';

export function useSecurityTabData() {
  const [bans, setBans] = useState<SecurityStrikesResponse[]>([]);
  const [stats, setStats] = useState<SecurityStatsResponse | null>(null);
  const [userInfoMap, setUserInfoMap] = useState<Record<string, UserInfoResponse>>({});
  const [loading, setLoading] = useState(true);
  const [clearDialog, setClearDialog] = useState<SecurityStrikesResponse | null>(null);
  const [clearReason, setClearReason] = useState('');
  const [clearing, setClearing] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [bansData, statsData] = await Promise.all([
        SecurityAPI.getActiveBans(),
        SecurityAPI.getStats(),
      ]);
      setBans(bansData);
      setStats(statsData);

      const results = await Promise.all(
        extractSecurityUserIds(bansData).map(async (userId) => {
          try {
            const info = await SecurityAPI.getUserInfo(userId);
            return { userId, info };
          } catch {
            return null;
          }
        })
      );

      setUserInfoMap(buildSecurityUserInfoMap(results));
    } catch (error) {
      console.error('Failed to fetch security data:', error);
      toast.error('Не удалось загрузить данные безопасности');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const handleClearStrikes = useCallback(async () => {
    if (!clearDialog) {
      return;
    }

    setClearing(true);
    try {
      await SecurityAPI.clearStrikes(clearDialog.identifier, clearReason);
      toast.success('Страйки очищены');
      setClearDialog(null);
      setClearReason('');
      await fetchData();
    } catch (error) {
      console.error('Failed to clear strikes:', error);
      toast.error('Не удалось очистить страйки');
    } finally {
      setClearing(false);
    }
  }, [clearDialog, clearReason, fetchData]);

  return {
    bans,
    stats,
    userInfoMap,
    loading,
    fetchData,
    clearDialog,
    setClearDialog,
    clearReason,
    setClearReason,
    clearing,
    handleClearStrikes,
  };
}
