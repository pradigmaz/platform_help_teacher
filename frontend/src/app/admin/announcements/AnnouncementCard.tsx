'use client';

import { AlertCircle, Eye, FileText, Loader2, Pencil, RotateCcw, Send, Trash2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BlurFade } from '@/components/ui/blur-fade';
import type { AdminAnnouncement } from '@/lib/api/admin-announcements';

import {
  canDeleteAnnouncement,
  canPublishAnnouncement,
  canSendAnnouncement,
  getAnnouncementBadgeVariant,
  getAnnouncementDeliverySummary,
  getAnnouncementStatusLabel,
  isAnnouncementEditable,
} from './announcement-status';
import { getAnnouncementPreview } from './announcement-preview';

interface AnnouncementCardProps {
  announcement: AdminAnnouncement;
  delay: number;
  loadingAction: 'publishing' | 'sending' | null;
  onEdit: () => void;
  onDelete?: () => void;
  onPublish?: () => void;
  onSend?: () => void;
}

export function AnnouncementCard({
  announcement,
  delay,
  loadingAction,
  onEdit,
  onDelete,
  onPublish,
  onSend,
}: AnnouncementCardProps) {
  const deliverySummary = getAnnouncementDeliverySummary(announcement);
  const preview = getAnnouncementPreview(announcement.content);
  const showSendAction = canSendAnnouncement(announcement) && onSend;
  const showPublishAction = canPublishAnnouncement(announcement) && onPublish;
  const showDeleteAction = canDeleteAnnouncement(announcement) && onDelete;
  const showEditAction = isAnnouncementEditable(announcement);
  const isSending = loadingAction === 'sending';
  const isPublishing = loadingAction === 'publishing';

  return (
    <BlurFade delay={delay}>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-purple-500" />
              <CardTitle className="text-lg">{announcement.title}</CardTitle>
            </div>
            <Badge variant={getAnnouncementBadgeVariant(announcement)}>
              {getAnnouncementStatusLabel(announcement)}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {announcement.author_name || 'Автор неизвестен'}
            {' • '}
            {new Date(announcement.published_at || announcement.created_at).toLocaleDateString('ru', {
              day: 'numeric',
              month: 'short',
              year: 'numeric',
            })}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground line-clamp-3">{preview}</p>

          {deliverySummary && (
            <div className="rounded-md border border-border/60 bg-muted/30 p-3 text-xs text-muted-foreground">
              <div className="flex items-center gap-2 font-medium text-foreground">
                <AlertCircle className="h-3.5 w-3.5" />
                Статус доставки
              </div>
              <p className="mt-1 leading-relaxed">{deliverySummary}</p>
            </div>
          )}

          <div className="flex flex-wrap gap-2 border-t pt-2">
            {showEditAction && (
              <Button size="sm" variant="outline" onClick={onEdit} className="gap-1">
                <Pencil className="h-3.5 w-3.5" />
                Редактировать
              </Button>
            )}

            {showPublishAction && (
              <Button size="sm" variant="default" onClick={onPublish} disabled={isPublishing} className="gap-1">
                {isPublishing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Eye className="h-3.5 w-3.5" />}
                Опубликовать
              </Button>
            )}

            {showSendAction && (
              <Button size="sm" variant="secondary" onClick={onSend} disabled={isSending} className="gap-1">
                {announcement.send_status === 'failed' ? (
                  <RotateCcw className="h-3.5 w-3.5" />
                ) : isSending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
                {announcement.send_status === 'failed' ? 'Повторить отправку' : 'Отправить'}
              </Button>
            )}

            {announcement.send_status === 'sending' && (
              <Button size="sm" variant="outline" disabled className="gap-1">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Отправляется...
              </Button>
            )}

            {showDeleteAction && (
              <Button
                size="sm"
                variant="ghost"
                onClick={onDelete}
                className="gap-1 text-destructive hover:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </BlurFade>
  );
}
