'use client';

import * as React from 'react';
import {
  AnnouncementsAPI,
  type Announcement,
  clearAllAnnouncements,
  getUnreadCount,
  markAnnouncementAsRead,
} from '@/lib/api/announcements';

interface NotificationBellSnapshot {
  announcements: Announcement[];
  unreadCount: number;
  loading: boolean;
}

const POLL_INTERVAL_MS = 5 * 60 * 1000;

let snapshot: NotificationBellSnapshot = {
  announcements: [],
  unreadCount: 0,
  loading: true,
};
let snapshotUpdatedAt = 0;
let inFlightLoad: Promise<void> | null = null;
let poller: ReturnType<typeof setInterval> | null = null;
let subscriberCount = 0;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

function updateSnapshot(nextSnapshot: NotificationBellSnapshot) {
  snapshot = nextSnapshot;
  snapshotUpdatedAt = Date.now();
  emit();
}

async function loadAnnouncements() {
  if (inFlightLoad) {
    return inFlightLoad;
  }

  inFlightLoad = (async () => {
    try {
      const announcements = await AnnouncementsAPI.getAnnouncements(0, 10);
      updateSnapshot({
        announcements,
        unreadCount: getUnreadCount(announcements),
        loading: false,
      });
    } catch {
      if (snapshot.loading) {
        updateSnapshot({
          ...snapshot,
          loading: false,
        });
      }
    } finally {
      inFlightLoad = null;
    }
  })();

  return inFlightLoad;
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  subscriberCount += 1;

  if (subscriberCount === 1) {
    if (snapshot.loading || Date.now() - snapshotUpdatedAt >= POLL_INTERVAL_MS) {
      void loadAnnouncements();
    }
    poller = setInterval(() => {
      void loadAnnouncements();
    }, POLL_INTERVAL_MS);
  }

  return () => {
    listeners.delete(listener);
    subscriberCount = Math.max(0, subscriberCount - 1);

    if (subscriberCount === 0 && poller) {
      clearInterval(poller);
      poller = null;
    }

    if (subscriberCount === 0) {
      inFlightLoad = null;
    }
  };
}

export function useNotificationBellState() {
  const currentSnapshot = React.useSyncExternalStore(
    subscribe,
    () => snapshot,
    () => snapshot,
  );

  const markAllAsRead = React.useCallback(() => {
    currentSnapshot.announcements.forEach((announcement) => {
      markAnnouncementAsRead(announcement.id);
    });

    updateSnapshot({
      ...snapshot,
      unreadCount: 0,
    });
  }, [currentSnapshot.announcements]);

  const dismissAnnouncement = React.useCallback((id: string) => {
    markAnnouncementAsRead(id);

    const announcements = snapshot.announcements.filter((announcement) => announcement.id !== id);
    updateSnapshot({
      announcements,
      unreadCount: getUnreadCount(announcements),
      loading: false,
    });
  }, []);

  const clearAnnouncements = React.useCallback(() => {
    clearAllAnnouncements();
    updateSnapshot({
      announcements: [],
      unreadCount: 0,
      loading: false,
    });
  }, []);

  return {
    ...currentSnapshot,
    markAllAsRead,
    dismissAnnouncement,
    clearAnnouncements,
  };
}

export function hydrateNotificationBellStore(announcements: Announcement[]) {
  updateSnapshot({
    announcements,
    unreadCount: getUnreadCount(announcements),
    loading: false,
  });
}

export function resetNotificationBellStoreForTests() {
  if (poller) {
    clearInterval(poller);
    poller = null;
  }

  inFlightLoad = null;
  subscriberCount = 0;
  listeners.clear();
  snapshot = {
    announcements: [],
    unreadCount: 0,
    loading: true,
  };
  snapshotUpdatedAt = 0;
}
