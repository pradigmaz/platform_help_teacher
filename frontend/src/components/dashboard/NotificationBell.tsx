'use client';

import { useEffect, useState, useCallback } from 'react';
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
  AnnouncementsAPI,
  Announcement,
  getReadAnnouncementIds,
  markAnnouncementAsRead,
  getUnreadCount,
  clearAllAnnouncements,
} from '@/lib/api/announcements';

interface NotificationBellProps {
  onOpenChange?: (open: boolean) => void;
}

export function NotificationBell({ onOpenChange }: NotificationBellProps) {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadAnnouncements = useCallback(async () => {
    try {
      const data = await AnnouncementsAPI.getAnnouncements(0, 10);
      setAnnouncements(data);
      setUnreadCount(getUnreadCount(data));
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnnouncements();
    // Обновляем каждые 5 минут
    const interval = setInterval(loadAnnouncements, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadAnnouncements]);

  const handleOpen = (isOpen: boolean) => {
    setOpen(isOpen);
    onOpenChange?.(isOpen);
    if (isOpen && announcements.length > 0) {
      // Помечаем все как прочитанные при открытии
      announcements.forEach(a => markAnnouncementAsRead(a.id));
      setUnreadCount(0);
    }
  };

  const handleClearAll = () => {
    clearAllAnnouncements();
    setAnnouncements([]);
    setUnreadCount(0);
  };

  const handleDismiss = (id: string) => {
    setAnnouncements(prev => prev.filter(a => a.id !== id));
    markAnnouncementAsRead(id);
    setUnreadCount(prev => Math.max(0, prev - 1));
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
                  onDismiss={handleDismiss}
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
        <button 
          onClick={() => setExpanded(!expanded)}
          className={cn("flex-1 min-w-0 text-left", isRead && "ml-4")}
        >
          <div className="flex items-start justify-between gap-2">
            <h5 className="font-medium text-sm flex-1">
              {announcement.title}
            </h5>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 shrink-0 hover:bg-destructive/10"
              onClick={(e) => {
                e.stopPropagation();
                onDismiss(announcement.id);
              }}
            >
              <IconX className="h-3 w-3 text-muted-foreground hover:text-destructive" />
            </Button>
          </div>
          
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
      </div>
    </div>
  );
}

