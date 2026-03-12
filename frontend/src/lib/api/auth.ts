import { api } from './client';
import type { AuthResponse, User } from './types';

export const AuthAPI = {
  login: async (
    otp: string,
    rememberDevice: boolean = false,
    forceSessionCookie: boolean = false,
  ) => {
    const { data } = await api.post<AuthResponse>('/auth/otp', {
      otp,
      remember_device: rememberDevice,
      force_session_cookie: forceSessionCookie,
    });
    return data;
  },

  devLogin: async (rememberDevice: boolean = true) => {
    const { data } = await api.post<AuthResponse>('/auth/dev-login', { remember_device: rememberDevice });
    return data;
  },
  
  logout: async () => {
    await api.post('/auth/logout');
  },

  me: async () => {
    const { data } = await api.get<User>('/users/me');
    return data;
  }
};
