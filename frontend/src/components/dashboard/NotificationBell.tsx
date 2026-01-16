'use client';

import { useEffect, useState, useCallback } from 'react';
import { IconBell } from '@tabler/icons-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
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
      <PopoverContent className="w-80 p-0" align="end">
        <div className="p-3 border-b">
          <h4 className="font-semibold text-sm">Объявления</h4>
        </div>
        <ScrollArea className="h-[300px]">
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
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}

function AnnouncementItem({ announcement, isRead }: { 
  announcement: Announcement; 
  isRead: boolean;
}) {
  const timeAgo = announcement.published_at
    ? formatDistanceToNow(new Date(announcement.published_at), { addSuffix: true, locale: ru })
    : '';

  return (
    <div className={cn(
      "p-3 hover:bg-accent/50 transition-colors cursor-default",
      !isRead && "bg-primary/5"
    )}>
      <div className="flex items-start gap-2">
        {!isRead && (
          <span className="mt-1.5 h-2 w-2 rounded-full bg-primary shrink-0" />
        )}
        <div className={cn("flex-1 min-w-0", isRead && "ml-4")}>
          <p className="font-medium text-sm truncate">{announcement.title}</p>
          <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
            {announcement.content}
          </p>
          {timeAgo && (
            <p className="text-xs text-muted-foreground mt-1">{timeAgo}</p>
          )}
        </div>
      </div>
    </div>
  );
}
