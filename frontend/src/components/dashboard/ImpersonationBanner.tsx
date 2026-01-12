'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AlertTriangle, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import api from '@/lib/api';

/**
 * Banner shown when admin is impersonating a student.
 * Checks for admin_original_token cookie presence.
 */
export function ImpersonationBanner() {
  const router = useRouter();
  const [isImpersonating, setIsImpersonating] = useState(false);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    // Check if admin_original_token cookie exists
    const hasAdminToken = document.cookie.includes('admin_original_token');
    setIsImpersonating(hasAdminToken);
  }, []);

  const handleExit = async () => {
    try {
      setExiting(true);
      await api.post('/admin/impersonate/exit');
      toast.success('Возврат в админку');
      router.push('/admin');
    } catch {
      toast.error('Не удалось выйти. Войдите заново.');
      router.push('/auth/login');
    } finally {
      setExiting(false);
    }
  };

  if (!isImpersonating) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-500 text-yellow-950 px-4 py-2">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span className="text-sm font-medium">
            Вы просматриваете систему от имени студента (сессия 15 мин)
          </span>
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
