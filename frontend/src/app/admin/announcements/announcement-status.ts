import type { AdminAnnouncement } from '@/lib/api/admin-announcements';

export function isAnnouncementEditable(announcement: AdminAnnouncement): boolean {
  return announcement.send_status !== 'sent' && announcement.send_status !== 'sending';
}

export function canDeleteAnnouncement(announcement: AdminAnnouncement): boolean {
  return announcement.is_draft;
}

export function canPublishAnnouncement(announcement: AdminAnnouncement): boolean {
  return announcement.is_draft;
}

export function canSendAnnouncement(announcement: AdminAnnouncement): boolean {
  return !announcement.is_draft && (announcement.send_status === 'not_sent' || announcement.send_status === 'failed');
}

export function needsAnnouncementPolling(announcements: AdminAnnouncement[]): boolean {
  return announcements.some((announcement) => announcement.send_status === 'sending');
}

export function getAnnouncementStatusLabel(announcement: AdminAnnouncement): string {
  if (announcement.is_draft) {
    return 'Черновик';
  }

  switch (announcement.send_status) {
    case 'sending':
      return 'Отправляется';
    case 'sent':
      return 'Отправлено';
    case 'failed':
      return 'Ошибка отправки';
    case 'not_sent':
    default:
      return 'Опубликовано';
  }
}

export function getAnnouncementBadgeVariant(
  announcement: AdminAnnouncement,
): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (announcement.is_draft) {
    return 'secondary';
  }
  if (announcement.send_status === 'failed') {
    return 'destructive';
  }
  if (announcement.send_status === 'sending') {
    return 'outline';
  }
  return 'default';
}

export function getAnnouncementDeliverySummary(announcement: AdminAnnouncement): string | null {
  if (announcement.delivery_error) {
    return announcement.delivery_error;
  }

  if (!announcement.delivery_stats) {
    return null;
  }

  const { telegram_sent, vk_sent, skipped, errors } = announcement.delivery_stats;
  return `Telegram ${telegram_sent}, VK ${vk_sent}, пропущено ${skipped}, ошибок ${errors}`;
}
