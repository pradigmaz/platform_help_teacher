'use client';

import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  IconDeviceDesktop, IconDeviceMobile, IconDeviceLaptop,
  IconTrash, IconRefresh, IconCheck, IconAlertCircle,
} from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { DevicesAPI, Device } from '@/lib/api/devices';
import { cn } from '@/lib/utils';

function pluralDevices(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `${count} устройство`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return `${count} устройства`;
  return `${count} устройств`;
}

export function DevicesSection() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const loadDevices = useCallback(async () => {
    console.log('[DevicesSection] Loading devices...');
    setError(false);
    try {
      const result = await DevicesAPI.getDevices();
      setDevices(result.devices);
    } catch (err) {
      console.error('[DevicesSection] Error loading devices:', err);
      setError(true);
      toast.error('Ошибка загрузки устройств');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDevices();
  }, [loadDevices]);

  const handleConfirm = async (deviceId: string) => {
    setActionInProgress(deviceId);
    try {
      await DevicesAPI.confirmDevice(deviceId);
      toast.success('Устройство подтверждено');
      loadDevices();
    } catch (error) {
      console.error('[DevicesSection] Error confirming device:', error);
      toast.error('Ошибка подтверждения устройства');
    } finally {
      setActionInProgress(null);
    }
  };

  const handleDelete = async (deviceId: string) => {
    if (!confirm('Отвязать это устройство?')) return;
    setActionInProgress(deviceId);
    try {
      await DevicesAPI.deleteDevice(deviceId);
      toast.success('Устройство отвязано');
      loadDevices();
    } catch (error) {
      console.error('[DevicesSection] Error deleting device:', error);
      toast.error('Ошибка отвязки устройства');
    } finally {
      setActionInProgress(null);
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

  if (error) {
    return (
      <div className="text-center py-8 space-y-3">
        <p className="text-sm text-muted-foreground">Не удалось загрузить устройства</p>
        <Button variant="outline" size="sm" onClick={loadDevices}>
          <IconRefresh className="h-4 w-4 mr-2" />
          Повторить
        </Button>
      </div>
    );
  }

  const trustedDevices = devices.filter(d => d.is_trusted);
  const untrustedDevices = devices.filter(d => !d.is_trusted);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold text-foreground">Привязанные устройства</h4>
          <p className="text-sm text-muted-foreground">{pluralDevices(devices.length)}</p>
        </div>
        <Button variant="ghost" size="icon" onClick={loadDevices} disabled={loading}>
          <IconRefresh className={cn("h-4 w-4", loading && "animate-spin")} />
        </Button>
      </div>

      {untrustedDevices.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400">
            <IconAlertCircle className="h-4 w-4" />
            <span className="font-medium">Требуют подтверждения</span>
          </div>
          {untrustedDevices.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              onConfirm={() => handleConfirm(device.id)}
              onDelete={() => handleDelete(device.id)}
              actionInProgress={actionInProgress === device.id}
            />
          ))}
        </div>
      )}

      {trustedDevices.length > 0 && (
        <div className="space-y-2">
          {untrustedDevices.length > 0 && (
            <div className="text-sm text-muted-foreground font-medium mt-4">Подтверждённые</div>
          )}
          {trustedDevices.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              onDelete={() => handleDelete(device.id)}
              actionInProgress={actionInProgress === device.id}
            />
          ))}
        </div>
      )}

      {devices.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">Нет привязанных устройств</div>
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

  const DeviceIcon = device_info.platform?.includes('Android') || device_info.platform?.includes('iOS')
    ? IconDeviceMobile
    : device_info.platform?.includes('Mac')
    ? IconDeviceLaptop
    : IconDeviceDesktop;

  const firstSeenAgo = formatDistanceToNow(new Date(first_seen), { addSuffix: true, locale: ru });
  const lastSeenAgo = formatDistanceToNow(new Date(last_seen), { addSuffix: true, locale: ru });

  return (
    <div className={cn(
      "flex items-center gap-4 p-3 rounded-lg border",
      is_trusted
        ? "bg-neutral-50 dark:bg-neutral-900/50 border-neutral-200 dark:border-neutral-800"
        : "bg-amber-500/5 border-amber-500/20"
    )}>
      <div className={cn("p-2 rounded-lg", is_trusted ? "bg-neutral-500/10" : "bg-amber-500/10")}>
        <DeviceIcon className={cn("h-5 w-5", is_trusted ? "text-neutral-500" : "text-amber-500")} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm truncate">
            {device_info.platform || 'Unknown'} • {device_info.browser || 'Unknown'}
          </span>
          {is_trusted && (
            <span className="px-1.5 py-0.5 rounded text-xs bg-green-500/10 text-green-600 dark:text-green-400 flex items-center gap-1">
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
            <IconCheck className={cn("h-4 w-4", actionInProgress && "animate-spin")} />
            Подтвердить
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="text-destructive hover:text-destructive hover:bg-destructive/10"
          onClick={onDelete}
          disabled={actionInProgress}
        >
          <IconTrash className={cn("h-4 w-4", actionInProgress && "animate-spin")} />
        </Button>
      </div>
    </div>
  );
}
