'use client';

import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  IconCheck,
  IconDeviceDesktop,
  IconDeviceLaptop,
  IconDeviceMobile,
  IconLogout,
  IconRefresh,
  IconTrash,
} from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { type Session, type SessionListResponse } from '@/lib/api/sessions';
import { cn } from '@/lib/utils';

interface SessionsSectionProps {
  data: SessionListResponse | null;
  loading: boolean;
  refreshing: boolean;
  onRefresh: () => void;
  onRevoke: (sessionId: string) => void;
  onRevokeAll: () => void;
  revokingSessionId: string | null;
  revokingAll: boolean;
}

export function SessionsSection({
  data,
  loading,
  refreshing,
  onRefresh,
  onRevoke,
  onRevokeAll,
  revokingSessionId,
  revokingAll,
}: SessionsSectionProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  const sessions = data?.sessions ?? [];
  const otherSessions = sessions.filter((session) => !session.is_current);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold text-foreground">Активные сессии</h4>
          <p className="text-sm text-muted-foreground">
            {data?.total ?? 0} из {data?.max_sessions ?? 5} устройств
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={onRefresh} disabled={refreshing}>
          <IconRefresh className={cn('h-4 w-4', refreshing && 'animate-spin')} />
        </Button>
      </div>

      <div className="space-y-2">
        {sessions.map((session) => (
          <SessionCard
            key={session.session_id}
            session={session}
            onRevoke={() => onRevoke(session.session_id)}
            revoking={revokingSessionId === session.session_id}
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
            onClick={onRevokeAll}
            disabled={revokingAll}
          >
            <IconLogout className={cn('h-4 w-4', revokingAll && 'animate-spin')} />
            Завершить все кроме текущей
          </Button>
        </>
      )}
    </div>
  );
}

function SessionCard({
  session,
  onRevoke,
  revoking,
}: {
  session: Session;
  onRevoke: () => void;
  revoking: boolean;
}) {
  const { device, ip_address, created_at, is_current } = session;

  const DeviceIcon =
    device.platform?.includes('Android') || device.platform?.includes('iOS')
      ? IconDeviceMobile
      : device.platform?.includes('Mac')
        ? IconDeviceLaptop
        : IconDeviceDesktop;

  const timeAgo = formatDistanceToNow(new Date(created_at), { addSuffix: true, locale: ru });

  return (
    <div
      className={cn(
        'flex items-center gap-4 rounded-lg border p-3',
        is_current
          ? 'border-green-500/20 bg-green-500/5'
          : 'border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-900/50',
      )}
    >
      <div className={cn('rounded-lg p-2', is_current ? 'bg-green-500/10' : 'bg-neutral-500/10')}>
        <DeviceIcon className={cn('h-5 w-5', is_current ? 'text-green-500' : 'text-neutral-500')} />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium">
            {device.platform || 'Unknown'} • {device.browser || 'Unknown'}
          </span>
          {is_current && (
            <span className="flex items-center gap-1 rounded bg-green-500/10 px-1.5 py-0.5 text-xs text-green-600 dark:text-green-400">
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
          className="text-destructive hover:bg-destructive/10 hover:text-destructive"
          onClick={onRevoke}
          disabled={revoking}
        >
          <IconTrash className={cn('h-4 w-4', revoking && 'animate-spin')} />
        </Button>
      )}
    </div>
  );
}
