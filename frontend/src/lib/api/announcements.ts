import { api } from './client';

export interface Announcement {
  id: string;
  title: string;
  content: string;
  is_draft: boolean;
  published_at: string | null;
  created_at: string;
}

export const AnnouncementsAPI = {
  getAnnouncements: async (skip = 0, limit = 20): Promise<Announcement[]> => {
    const { data } = await api.get<Announcement[]>('/student/announcements', {
      params: { skip, limit }
    });
    return data;
  },
};

// LocalStorage для отслеживания прочитанных
const READ_KEY = 'read_announcements';

export function getReadAnnouncementIds(): Set<string> {
  if (typeof window === 'undefined') return new Set();
  try {
    const stored = localStorage.getItem(READ_KEY);
    return new Set(stored ? JSON.parse(stored) : []);
  } catch {
    return new Set();
  }
}

export function markAnnouncementAsRead(id: string): void {
  if (typeof window === 'undefined') return;
  const read = getReadAnnouncementIds();
  read.add(id);
  // Храним только последние 100
  const arr = Array.from(read).slice(-100);
  localStorage.setItem(READ_KEY, JSON.stringify(arr));
}

export function getUnreadCount(announcements: Announcement[]): number {
  const read = getReadAnnouncementIds();
  return announcements.filter(a => !read.has(a.id)).length;
}

export function clearAllAnnouncements(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(READ_KEY);
}
