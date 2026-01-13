/**
 * Async data collectors (media devices, storage, battery, permissions).
 */
import type { DeviceFingerprint, MediaDevicesInfo, StorageInfo, BatteryInfo, PermissionsInfo } from './types';

export async function getMediaDevicesInfo(): Promise<MediaDevicesInfo | undefined> {
  try {
    if (!navigator.mediaDevices?.enumerateDevices) return undefined;
    const devices = await navigator.mediaDevices.enumerateDevices();
    return {
      cameras: devices.filter(d => d.kind === 'videoinput').length,
      microphones: devices.filter(d => d.kind === 'audioinput').length,
      speakers: devices.filter(d => d.kind === 'audiooutput').length,
      deviceIds: devices.map(d => d.deviceId).filter(Boolean).slice(0, 10),
    };
  } catch {
    return undefined;
  }
}

export async function getStorageInfo(): Promise<StorageInfo | undefined> {
  try {
    if (!navigator.storage?.estimate) return undefined;
    const estimate = await navigator.storage.estimate();
    return {
      quota: estimate.quota,
      usage: estimate.usage,
      persistent: await navigator.storage.persisted?.() ?? undefined,
    };
  } catch {
    return undefined;
  }
}

interface BatteryManager {
  charging: boolean;
  level: number;
  chargingTime: number;
  dischargingTime: number;
}

interface NavigatorWithBattery extends Navigator {
  getBattery?: () => Promise<BatteryManager>;
}

export async function getBatteryInfo(): Promise<BatteryInfo | undefined> {
  try {
    const nav = navigator as NavigatorWithBattery;
    if (!nav.getBattery) return undefined;
    const battery = await nav.getBattery();
    return {
      charging: battery.charging,
      level: battery.level,
      chargingTime: battery.chargingTime,
      dischargingTime: battery.dischargingTime,
    };
  } catch {
    return undefined;
  }
}

export async function getPermissionsInfo(): Promise<PermissionsInfo | undefined> {
  try {
    if (!navigator.permissions) return undefined;
    const perms: PermissionsInfo = {};
    
    try { perms.notifications = (await navigator.permissions.query({ name: 'notifications' })).state; } catch {}
    try { perms.geolocation = (await navigator.permissions.query({ name: 'geolocation' })).state; } catch {}
    try { perms.camera = (await navigator.permissions.query({ name: 'camera' as PermissionName })).state; } catch {}
    try { perms.microphone = (await navigator.permissions.query({ name: 'microphone' as PermissionName })).state; } catch {}
    
    return perms;
  } catch {
    return undefined;
  }
}

export async function enrichWithAsyncData(base: DeviceFingerprint): Promise<DeviceFingerprint> {
  try {
    const [mediaDevices, storage, battery, permissions] = await Promise.all([
      getMediaDevicesInfo(),
      getStorageInfo(),
      getBatteryInfo(),
      getPermissionsInfo(),
    ]);
    
    return {
      ...base,
      mediaDevices,
      storage,
      battery,
      permissions,
      performanceTiming: performance.timing ? {
        navigationStart: performance.timing.navigationStart,
        loadEventEnd: performance.timing.loadEventEnd,
      } : undefined,
    };
  } catch {
    return base;
  }
}
