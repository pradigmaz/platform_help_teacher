'use client';

import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  IconAlertCircle,
  IconCheck,
  IconDeviceDesktop,
  IconDeviceLaptop,
  IconDeviceMobile,
  IconRefresh,
  IconTrash,
} from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { type Device } from '@/lib/api/devices';
import { cn } from '@/lib/utils';

interface DevicesSectionProps {
  devices: Device[];
  loading: boolean;
  error: boolean;
  refreshing: boolean;
  actionInProgressId: string | null;
  onRefresh: () => void;
  onConfirm: (deviceId: string) => void;
  onDelete: (deviceId: string) => void;
}

function pluralDevices(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `${count} устройство`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return `${count} устройства`;
  return `${count} устройств`;
}

export function DevicesSection({
  devices,
  loading,
  error,
  refreshing,
  actionInProgressId,
  onRefresh,
  onConfirm,
  onDelete,
}: DevicesSectionProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3 py-8 text-center">
        <p className="text-sm text-muted-foreground">Не удалось загрузить устройства</p>
        <Button variant="outline" size="sm" onClick={onRefresh}>
          <IconRefresh className="mr-2 h-4 w-4" />
          Повторить
        </Button>
      </div>
    );
  }

  const trustedDevices = devices.filter((device) => device.is_trusted);
  const untrustedDevices = devices.filter((device) => !device.is_trusted);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold text-foreground">Привязанные устройства</h4>
          <p className="text-sm text-muted-foreground">{pluralDevices(devices.length)}</p>
        </div>
        <Button variant="ghost" size="icon" onClick={onRefresh} disabled={refreshing}>
          <IconRefresh className={cn('h-4 w-4', refreshing && 'animate-spin')} />
        </Button>
      </div>

      {untrustedDevices.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-amber-600 dark:text-amber-400">
            <IconAlertCircle className="h-4 w-4" />
            Требуют подтверждения
          </div>
          {untrustedDevices.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              onConfirm={() => onConfirm(device.id)}
              onDelete={() => onDelete(device.id)}
              actionInProgress={actionInProgressId === device.id}
            />
          ))}
        </div>
      )}

      {trustedDevices.length > 0 && (
        <div className="space-y-2">
          {untrustedDevices.length > 0 && (
            <div className="mt-4 text-sm font-medium text-muted-foreground">Подтверждённые</div>
          )}
          {trustedDevices.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              onDelete={() => onDelete(device.id)}
              actionInProgress={actionInProgressId === device.id}
            />
          ))}
        </div>
      )}

      {devices.length === 0 && (
        <div className="py-8 text-center text-muted-foreground">Нет привязанных устройств</div>
      )}
    </div>
  );
}

function DeviceCard({
  device,
  onConfirm,
  onDelete,
  actionInProgress,
}: {
  device: Device;
  onConfirm?: () => void;
  onDelete: () => void;
  actionInProgress: boolean;
}) {
  const { device_info, first_seen, last_seen, is_trusted } = device;

  const DeviceIcon =
    device_info.platform?.includes('Android') || device_info.platform?.includes('iOS')
      ? IconDeviceMobile
      : device_info.platform?.includes('Mac')
        ? IconDeviceLaptop
        : IconDeviceDesktop;

  const firstSeenAgo = formatDistanceToNow(new Date(first_seen), { addSuffix: true, locale: ru });
  const lastSeenAgo = formatDistanceToNow(new Date(last_seen), { addSuffix: true, locale: ru });

  return (
    <div
      className={cn(
        'flex items-center gap-4 rounded-lg border p-3',
        is_trusted
          ? 'border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-900/50'
          : 'border-amber-500/20 bg-amber-500/5',
      )}
    >
      <div className={cn('rounded-lg p-2', is_trusted ? 'bg-neutral-500/10' : 'bg-amber-500/10')}>
        <DeviceIcon className={cn('h-5 w-5', is_trusted ? 'text-neutral-500' : 'text-amber-500')} />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium">
            {device_info.platform || 'Unknown'} • {device_info.browser || 'Unknown'}
          </span>
          {is_trusted && (
            <span className="flex items-center gap-1 rounded bg-green-500/10 px-1.5 py-0.5 text-xs text-green-600 dark:text-green-400">
              <IconCheck className="h-3 w-3" /> Подтверждено
            </span>
          )}
        </div>
        <div className="text-xs text-muted-foreground">
          Первый вход: {firstSeenAgo}
          {device_info.screen && <span> • {device_info.screen}</span>}
        </div>
        <div className="text-xs text-muted-foreground">Последний вход: {lastSeenAgo}</div>
      </div>

      <div className="flex items-center gap-2">
        {!is_trusted && onConfirm && (
          <Button
            variant="default"
            size="sm"
            className="gap-1 bg-green-600 hover:bg-green-700"
            onClick={onConfirm}
            disabled={actionInProgress}
          >
            <IconCheck className={cn('h-4 w-4', actionInProgress && 'animate-spin')} />
            Подтвердить
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="text-destructive hover:bg-destructive/10 hover:text-destructive"
          onClick={onDelete}
          disabled={actionInProgress}
        >
          <IconTrash className={cn('h-4 w-4', actionInProgress && 'animate-spin')} />
        </Button>
      </div>
    </div>
  );
}
