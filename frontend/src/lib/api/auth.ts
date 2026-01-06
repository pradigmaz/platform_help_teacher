import { api, ensureCsrfToken } from './client';
import type { AuthResponse, User } from './types';

export const AuthAPI = {
  login: async (otp: string) => {
    const token = await ensureCsrfToken();
    const { data } = await api.post<AuthResponse>('/auth/otp', { otp }, {
      headers: { 'X-CSRF-Token': token }
    });
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
