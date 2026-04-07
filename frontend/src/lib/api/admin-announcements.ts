import { api } from './client';

export type AnnouncementSendStatus = 'not_sent' | 'sending' | 'sent' | 'failed';

export interface AnnouncementDeliveryStats {
  telegram_sent: number;
  vk_sent: number;
  skipped: number;
  errors: number;
}

export interface AdminAnnouncement {
  id: string;
  title: string;
  content: string;
  author_name: string | null;
  created_by?: string | null;
  is_draft: boolean;
  send_status: AnnouncementSendStatus;
  published_at: string | null;
  send_started_at: string | null;
  sent_at: string | null;
  sent_by?: string | null;
  created_at: string;
  updated_at: string;
  delivery_stats: AnnouncementDeliveryStats | null;
  delivery_error: string | null;
}

export interface AnnouncementPayload {
  title: string;
  content: string;
}

export const AdminAnnouncementsAPI = {
  list: async (): Promise<AdminAnnouncement[]> => {
    const { data } = await api.get<AdminAnnouncement[]>('/admin/announcements');
    return data;
  },

  get: async (announcementId: string): Promise<AdminAnnouncement> => {
    const { data } = await api.get<AdminAnnouncement>(`/admin/announcements/${announcementId}`);
    return data;
  },

  create: async (payload: AnnouncementPayload): Promise<AdminAnnouncement> => {
    const { data } = await api.post<AdminAnnouncement>('/admin/announcements', payload);
    return data;
  },

  update: async (announcementId: string, payload: AnnouncementPayload): Promise<AdminAnnouncement> => {
    const { data } = await api.put<AdminAnnouncement>(`/admin/announcements/${announcementId}`, payload);
    return data;
  },

  delete: async (announcementId: string): Promise<void> => {
    await api.delete(`/admin/announcements/${announcementId}`);
  },

  publish: async (announcementId: string): Promise<AdminAnnouncement> => {
    const { data } = await api.post<AdminAnnouncement>(`/admin/announcements/${announcementId}/publish`);
    return data;
  },

  send: async (announcementId: string): Promise<AdminAnnouncement> => {
    const { data } = await api.post<AdminAnnouncement>(`/admin/announcements/${announcementId}/send`);
    return data;
  },
};
