import { api } from './client';

export interface DeviceInfo {
  platform: string | null;
  browser: string | null;
  screen: string | null;
}

export interface Device {
  id: string;
  user_id: string;
  device_info: DeviceInfo;
  first_seen: string;
  last_seen: string;
  is_trusted: boolean;
  confirmed_at: string | null;
}

export interface DeviceListResponse {
  devices: Device[];
  total: number;
}

export const DevicesAPI = {
  getDevices: async (): Promise<DeviceListResponse> => {
    const { data } = await api.get<DeviceListResponse>('/users/me/devices');
    return data;
  },

  confirmDevice: async (deviceId: string): Promise<Device> => {
    const { data } = await api.post<Device>(`/users/me/devices/${deviceId}/confirm`);
    return data;
  },

  deleteDevice: async (deviceId: string): Promise<void> => {
    await api.delete(`/users/me/devices/${deviceId}`);
  },
};
