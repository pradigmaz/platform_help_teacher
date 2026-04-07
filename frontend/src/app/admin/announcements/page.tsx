'use client';

import { useCallback, useEffect, useState } from 'react';
import { Loader2, Plus } from 'lucide-react';
import { toast } from 'sonner';

import { BlurFade } from '@/components/ui/blur-fade';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { AdminAnnouncementsAPI, type AdminAnnouncement } from '@/lib/api/admin-announcements';

import { AnnouncementCard } from './AnnouncementCard';
import { AnnouncementDialog } from './AnnouncementDialog';
import { needsAnnouncementPolling } from './announcement-status';

const POLL_INTERVAL_MS = 5_000;

type AnnouncementAction = {
  action: 'publishing' | 'sending';
  id: string;
} | null;

export default function AnnouncementsPage() {
  const [announcements, setAnnouncements] = useState<AdminAnnouncement[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<AnnouncementAction>(null);

  const fetchAnnouncements = useCallback(async (options?: { keepSpinner?: boolean }) => {
    if (!options?.keepSpinner) {
      setLoading(true);
    }

    try {
      const data = await AdminAnnouncementsAPI.list();
      setAnnouncements(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Ошибка загрузки объявлений';
      toast.error(message);
    } finally {
      if (!options?.keepSpinner) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void fetchAnnouncements();
  }, [fetchAnnouncements]);

  useEffect(() => {
    if (!needsAnnouncementPolling(announcements)) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void fetchAnnouncements({ keepSpinner: true });
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(intervalId);
  }, [announcements, fetchAnnouncements]);

  const handleCreate = () => {
    setEditingId(null);
    setDialogOpen(true);
  };

  const handleEdit = (id: string) => {
    setEditingId(id);
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить черновик?')) return;

    try {
      await AdminAnnouncementsAPI.delete(id);
      toast.success('Черновик удалён');
      await fetchAnnouncements({ keepSpinner: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Ошибка удаления';
      toast.error(message);
    }
  };

  const handlePublish = async (id: string) => {
    setPendingAction({ action: 'publishing', id });
    try {
      await AdminAnnouncementsAPI.publish(id);
      toast.success('Объявление опубликовано');
      await fetchAnnouncements({ keepSpinner: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Ошибка публикации';
      toast.error(message);
    } finally {
      setPendingAction(null);
    }
  };

  const handleSend = async (id: string) => {
    setPendingAction({ action: 'sending', id });
    try {
      await AdminAnnouncementsAPI.send(id);
      toast.success('Отправка поставлена в очередь');
      await fetchAnnouncements({ keepSpinner: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Ошибка отправки';
      toast.error(message);
    } finally {
      setPendingAction(null);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const drafts = announcements.filter((announcement) => announcement.is_draft);
  const published = announcements.filter((announcement) => !announcement.is_draft);

  return (
    <div className="space-y-6">
      <BlurFade delay={0.1}>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Объявления</h1>
          <Button onClick={handleCreate} className="gap-2">
            <Plus className="h-4 w-4" />
            Создать
          </Button>
        </div>
      </BlurFade>

      {drafts.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-muted-foreground">Черновики</h2>
          {drafts.map((announcement, index) => (
            <AnnouncementCard
              key={announcement.id}
              announcement={announcement}
              delay={0.15 + index * 0.05}
              loadingAction={
                pendingAction?.id === announcement.id ? pendingAction.action : null
              }
              onEdit={() => handleEdit(announcement.id)}
              onDelete={() => handleDelete(announcement.id)}
              onPublish={() => handlePublish(announcement.id)}
            />
          ))}
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-muted-foreground">Опубликованные</h2>
        {published.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              Нет опубликованных объявлений
            </CardContent>
          </Card>
        ) : (
          published.map((announcement, index) => (
            <AnnouncementCard
              key={announcement.id}
              announcement={announcement}
              delay={0.25 + index * 0.05}
              loadingAction={
                pendingAction?.id === announcement.id ? pendingAction.action : null
              }
              onEdit={() => handleEdit(announcement.id)}
              onSend={() => handleSend(announcement.id)}
            />
          ))
        )}
      </section>

      <AnnouncementDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        announcementId={editingId}
        onSuccess={() => void fetchAnnouncements({ keepSpinner: true })}
      />
    </div>
  );
}
