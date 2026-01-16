'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  IconDeviceDesktop, IconDeviceMobile, IconDeviceLaptop,
  IconTrash, IconLogout, IconRefresh, IconCheck,
} from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { SessionsAPI, Session, SessionListResponse } from '@/lib/api/sessions';
import { cn } from '@/lib/utils';

export function SessionsSection() {
  const [data, setData] = useState<SessionListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [revokingAll, setRevokingAll] = useState(false);

  const loadSessions = async () => {
    try {
      const result = await SessionsAPI.getSessions();
      setData(result);
    } catch {
      toast.error('Ошибка загрузки сессий');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleRevoke = async (sessionId: string) => {
    setRevoking(sessionId);
    try {
      await SessionsAPI.revokeSession(sessionId);
      toast.success('Сессия завершена');
      loadSessions();
    } catch {
      toast.error('Ошибка завершения сессии');
    } finally {
      setRevoking(null);
    }
  };

  const handleRevokeAll = async () => {
    if (!confirm('Завершить все сессии кроме текущей?')) return;
    setRevokingAll(true);
    try {
      const result = await SessionsAPI.revokeAllSessions();
      toast.success(result.message);
      loadSessions();
    } catch {
      toast.error('Ошибка завершения сессий');
    } finally {
      setRevokingAll(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  const sessions = data?.sessions || [];
  const otherSessions = sessions.filter(s => !s.is_current);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold text-foreground">Активные сессии</h4>
          <p className="text-sm text-muted-foreground">
            {data?.total || 0} из {data?.max_sessions || 5} устройств
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={loadSessions} disabled={loading}>
          <IconRefresh className={cn("h-4 w-4", loading && "animate-spin")} />
        </Button>
      </div>

      <div className="space-y-2">
        {sessions.map((session) => (
          <SessionCard
            key={session.session_id}
            session={session}
            onRevoke={() => handleRevoke(session.session_id)}
            revoking={revoking === session.session_id}
          />
        ))}
      </div>

      {otherSessions.length > 0 && (
        <>
          <Separator className="bg-neutral-200 dark:bg-neutral-800" />
          <Button
            variant="destructive"
            size="sm"
            className="w-full gap-2"
            onClick={handleRevokeAll}
            disabled={revokingAll}
          >
            <IconLogout className={cn("h-4 w-4", revokingAll && "animate-spin")} />
            Завершить все кроме текущей
          </Button>
        </>
      )}
    </div>
  );
}

function SessionCard({ session, onRevoke, revoking }: {
  session: Session;
  onRevoke: () => void;
  revoking: boolean;
}) {
  const { device, ip_address, created_at, is_current } = session;
  
  const DeviceIcon = device.platform?.includes('Android') || device.platform?.includes('iOS')
    ? IconDeviceMobile
    : device.platform?.includes('Mac')
    ? IconDeviceLaptop
    : IconDeviceDesktop;

  const timeAgo = formatDistanceToNow(new Date(created_at), { addSuffix: true, locale: ru });

  return (
    <div className={cn(
      "flex items-center gap-4 p-3 rounded-lg border",
      is_current
        ? "bg-green-500/5 border-green-500/20"
        : "bg-neutral-50 dark:bg-neutral-900/50 border-neutral-200 dark:border-neutral-800"
    )}>
      <div className={cn(
        "p-2 rounded-lg",
        is_current ? "bg-green-500/10" : "bg-neutral-500/10"
      )}>
        <DeviceIcon className={cn("h-5 w-5", is_current ? "text-green-500" : "text-neutral-500")} />
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm truncate">
            {device.platform || 'Unknown'} • {device.browser || 'Unknown'}
          </span>
          {is_current && (
            <span className="px-1.5 py-0.5 rounded text-xs bg-green-500/10 text-green-600 dark:text-green-400 flex items-center gap-1">
              <IconCheck className="h-3 w-3" /> Текущая
            </span>
          )}
        </div>
        <div className="text-xs text-muted-foreground">
          {ip_address && <span>{ip_address} • </span>}
          {timeAgo}
          {device.screen && <span> • {device.screen}</span>}
        </div>
      </div>

      {!is_current && (
        <Button
          variant="ghost"
          size="icon"
          className="text-destructive hover:text-destructive hover:bg-destructive/10"
          onClick={onRevoke}
          disabled={revoking}
        >
          <IconTrash className={cn("h-4 w-4", revoking && "animate-spin")} />
        </Button>
      )}
    </div>
  );
}
