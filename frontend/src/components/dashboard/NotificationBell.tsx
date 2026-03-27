'use client';

import { useState } from 'react';
import { IconBell, IconX, IconTrash } from '@tabler/icons-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  getReadAnnouncementIds,
  type Announcement,
} from '@/lib/api/announcements';
import { useNotificationBellState } from './notification-bell-store';

interface NotificationBellProps {
  onOpenChange?: (open: boolean) => void;
}

export function NotificationBell({ onOpenChange }: NotificationBellProps) {
  const {
    announcements,
    unreadCount,
    loading,
    markAllAsRead,
    dismissAnnouncement,
    clearAnnouncements,
  } = useNotificationBellState();
  const [open, setOpen] = useState(false);

  const handleOpen = (isOpen: boolean) => {
    setOpen(isOpen);
    onOpenChange?.(isOpen);
    if (isOpen && announcements.length > 0) {
      markAllAsRead();
    }
  };

  const handleClearAll = () => {
    clearAnnouncements();
  };

  const readIds = getReadAnnouncementIds();

  return (
    <Popover open={open} onOpenChange={handleOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <IconBell className="h-5 w-5 text-muted-foreground" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-destructive text-[10px] font-medium text-destructive-foreground flex items-center justify-center">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96 p-0" align="end">
        <div className="p-3 border-b flex items-center justify-between">
          <h4 className="font-semibold text-sm">Объявления</h4>
          {announcements.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearAll}
              className="h-7 text-xs gap-1"
            >
              <IconTrash className="h-3 w-3" />
              Очистить
            </Button>
          )}
        </div>
        <ScrollArea className="h-[400px]">
          {loading ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              Загрузка...
            </div>
          ) : announcements.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              Нет объявлений
            </div>
          ) : (
            <div className="divide-y">
              {announcements.map((a) => (
                <AnnouncementItem
                  key={a.id}
                  announcement={a}
                  isRead={readIds.has(a.id)}
                  onDismiss={dismissAnnouncement}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}

function AnnouncementItem({ announcement, isRead, onDismiss }: { 
  announcement: Announcement; 
  isRead: boolean;
  onDismiss: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const timeAgo = announcement.published_at
    ? formatDistanceToNow(new Date(announcement.published_at), { addSuffix: true, locale: ru })
    : '';

  return (
    <div className={cn(
      "p-3 hover:bg-accent/50 transition-colors",
      !isRead && "bg-primary/5"
    )}>
      <div className="flex items-start gap-2">
        {!isRead && (
          <span className="mt-1.5 h-2 w-2 rounded-full bg-primary shrink-0" />
        )}
        <div className={cn("flex-1 min-w-0", isRead && "ml-4")}>
          <div className="flex items-start gap-2">
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              aria-expanded={expanded}
              className="flex-1 min-w-0 text-left"
            >
              <h5 className="font-medium text-sm">
                {announcement.title}
              </h5>

              <div className={cn(
                "text-xs text-muted-foreground mt-1 prose prose-sm dark:prose-invert max-w-none",
                !expanded && "line-clamp-2"
              )}>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeSanitize]}
                >
                  {announcement.content}
                </ReactMarkdown>
              </div>

              {timeAgo && (
                <p className="text-xs text-muted-foreground mt-1">{timeAgo}</p>
              )}
            </button>

            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-6 w-6 shrink-0 hover:bg-destructive/10"
              onClick={() => onDismiss(announcement.id)}
            >
              <IconX className="h-3 w-3 text-muted-foreground hover:text-destructive" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

