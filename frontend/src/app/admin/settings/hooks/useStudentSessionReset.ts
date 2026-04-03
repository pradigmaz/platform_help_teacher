'use client';

import { useCallback, useState } from 'react';
import { toast } from 'sonner';
import api from '@/lib/api';

export function useStudentSessionReset() {
  const [revokeLoading, setRevokeLoading] = useState(false);

  const handleRevokeAllStudentSessions = useCallback(async () => {
    if (!confirm('Выкинуть ВСЕХ студентов из всех сессий? Им придётся заново авторизоваться.')) {
      return;
    }

    setRevokeLoading(true);
    try {
      const { data } = await api.post('/admin/impersonate/sessions/revoke-all-students');
      toast.success(`Выкинуто ${data.sessions_revoked} сессий у ${data.students_count} студентов`);
    } catch {
      toast.error('Ошибка при выкидывании сессий');
    } finally {
      setRevokeLoading(false);
    }
  }, []);

  return {
    revokeLoading,
    handleRevokeAllStudentSessions,
  };
}
