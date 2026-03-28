'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { AlertTriangle, LogOut, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { AdminAPI } from '@/lib/api';
import { primeAuthFingerprint } from '@/lib/fingerprint/adapter';

const IMPERSONATE_TTL_MINUTES = 15;

/**
 * Banner shown when admin is impersonating a student.
 * Checks for 'impersonating' cookie presence (set by backend).
 */
export function ImpersonationBanner() {
  const router = useRouter();
  const [isImpersonating, setIsImpersonating] = useState(false);
  const [exiting, setExiting] = useState(false);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);

  // Get cookie creation time from localStorage or set it
  const getSessionStart = useCallback(() => {
    const stored = localStorage.getItem('impersonate_start');
    if (stored) return parseInt(stored, 10);
    const now = Date.now();
    localStorage.setItem('impersonate_start', now.toString());
    return now;
  }, []);

  useEffect(() => {
    const hasImpersonatingFlag = document.cookie.includes('impersonating=true');
    setIsImpersonating(hasImpersonatingFlag);
    
    if (!hasImpersonatingFlag) {
      localStorage.removeItem('impersonate_start');
      return;
    }

    void primeAuthFingerprint();

    const sessionStart = getSessionStart();
    const expiresAt = sessionStart + IMPERSONATE_TTL_MINUTES * 60 * 1000;

    const updateTimer = () => {
      const remaining = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
      setTimeLeft(remaining);
      
      if (remaining <= 0) {
        localStorage.removeItem('impersonate_start');
        toast.info('Сессия истекла');
        router.push('/auth/login');
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [getSessionStart, router]);

  const handleExit = async () => {
    try {
      setExiting(true);
      await AdminAPI.exitImpersonation();
      localStorage.removeItem('impersonate_start');
      toast.success('Возврат в админку');
      router.push('/admin');
    } catch {
      toast.error('Не удалось выйти. Войдите заново.');
      router.push('/auth/login');
    } finally {
      setExiting(false);
    }
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (!isImpersonating) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-500 text-yellow-950 px-4 py-2">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span className="text-sm font-medium">
            Вы просматриваете систему от имени студента
          </span>
          {timeLeft !== null && (
            <span className="flex items-center gap-1 text-sm font-mono bg-yellow-600/30 px-2 py-0.5 rounded">
              <Clock className="h-3 w-3" />
              {formatTime(timeLeft)}
            </span>
          )}
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={handleExit}
          disabled={exiting}
          className="bg-yellow-600 border-yellow-700 text-white hover:bg-yellow-700"
        >
          <LogOut className="h-4 w-4 mr-1" />
          {exiting ? 'Выход...' : 'Вернуться в админку'}
        </Button>
      </div>
    </div>
  );
}
