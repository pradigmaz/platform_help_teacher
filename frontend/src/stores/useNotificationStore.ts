import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  description?: string;
  duration?: number;
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationState>()(
  devtools(
    (set) => ({
      notifications: [],
      unreadCount: 0,

      addNotification: (notification) => {
        const id = typeof crypto?.randomUUID === 'function' 
          ? crypto.randomUUID() 
          : Date.now().toString(36) + Math.random().toString(36).slice(2);
        console.log('[Store:useNotificationStore] addNotification', { id, notification });
        set((state) => ({
          notifications: [...state.notifications, { ...notification, id }],
          unreadCount: state.unreadCount + 1,
        }));
      },

      removeNotification: (id) => {
        console.log('[Store:useNotificationStore] removeNotification', { id });
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
          unreadCount: Math.max(0, state.unreadCount - 1),
        }));
      },

      clearAll: () => {
        console.log('[Store:useNotificationStore] clearAll');
        set({ notifications: [], unreadCount: 0 });
      },
    }),
    { name: 'NotificationStore' }
  )
);
