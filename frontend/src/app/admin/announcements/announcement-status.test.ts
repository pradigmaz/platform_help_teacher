import { describe, expect, it } from 'vitest';

import type { AdminAnnouncement } from '@/lib/api/admin-announcements';

import {
  canDeleteAnnouncement,
  canPublishAnnouncement,
  canSendAnnouncement,
  getAnnouncementBadgeVariant,
  getAnnouncementStatusLabel,
  isAnnouncementEditable,
  needsAnnouncementPolling,
} from './announcement-status';

function makeAnnouncement(overrides: Partial<AdminAnnouncement> = {}): AdminAnnouncement {
  return {
    id: 'announcement-1',
    title: 'Новый регламент',
    content: 'Подробности',
    author_name: 'Преподаватель',
    is_draft: false,
    send_status: 'not_sent',
    published_at: '2026-04-07T09:00:00.000Z',
    send_started_at: null,
    sent_at: null,
    created_at: '2026-04-07T08:00:00.000Z',
    updated_at: '2026-04-07T08:00:00.000Z',
    delivery_stats: null,
    delivery_error: null,
    ...overrides,
  };
}

describe('announcement lifecycle helpers', () => {
  it('allows only draft deletion and publish', () => {
    const draft = makeAnnouncement({ is_draft: true });
    const published = makeAnnouncement();

    expect(canDeleteAnnouncement(draft)).toBe(true);
    expect(canPublishAnnouncement(draft)).toBe(true);
    expect(canDeleteAnnouncement(published)).toBe(false);
    expect(canPublishAnnouncement(published)).toBe(false);
  });

  it('locks editing after send and while sending', () => {
    expect(isAnnouncementEditable(makeAnnouncement({ send_status: 'not_sent' }))).toBe(true);
    expect(isAnnouncementEditable(makeAnnouncement({ send_status: 'failed' }))).toBe(true);
    expect(isAnnouncementEditable(makeAnnouncement({ send_status: 'sending' }))).toBe(false);
    expect(isAnnouncementEditable(makeAnnouncement({ send_status: 'sent' }))).toBe(false);
  });

  it('allows send only for published not_sent or failed announcements', () => {
    expect(canSendAnnouncement(makeAnnouncement({ send_status: 'not_sent' }))).toBe(true);
    expect(canSendAnnouncement(makeAnnouncement({ send_status: 'failed' }))).toBe(true);
    expect(canSendAnnouncement(makeAnnouncement({ send_status: 'sending' }))).toBe(false);
    expect(canSendAnnouncement(makeAnnouncement({ send_status: 'sent' }))).toBe(false);
    expect(canSendAnnouncement(makeAnnouncement({ is_draft: true, send_status: 'not_sent' }))).toBe(false);
  });

  it('computes labels, badge variants, and polling trigger from send status', () => {
    expect(getAnnouncementStatusLabel(makeAnnouncement({ is_draft: true }))).toBe('Черновик');
    expect(getAnnouncementStatusLabel(makeAnnouncement({ send_status: 'sending' }))).toBe('Отправляется');
    expect(getAnnouncementStatusLabel(makeAnnouncement({ send_status: 'sent' }))).toBe('Отправлено');
    expect(getAnnouncementStatusLabel(makeAnnouncement({ send_status: 'failed' }))).toBe('Ошибка отправки');

    expect(getAnnouncementBadgeVariant(makeAnnouncement({ is_draft: true }))).toBe('secondary');
    expect(getAnnouncementBadgeVariant(makeAnnouncement({ send_status: 'sending' }))).toBe('outline');
    expect(getAnnouncementBadgeVariant(makeAnnouncement({ send_status: 'failed' }))).toBe('destructive');
    expect(getAnnouncementBadgeVariant(makeAnnouncement({ send_status: 'sent' }))).toBe('default');

    expect(needsAnnouncementPolling([makeAnnouncement({ send_status: 'sending' })])).toBe(true);
    expect(needsAnnouncementPolling([makeAnnouncement({ send_status: 'sent' })])).toBe(false);
  });
});
