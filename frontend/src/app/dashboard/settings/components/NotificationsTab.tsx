'use client';

import { motion } from 'motion/react';
import { IconBrandVk, IconBrandTelegram, IconClock, IconStar, IconTool } from '@tabler/icons-react';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { cn } from '@/lib/utils';

interface NotificationsState {
  vk: boolean;
  telegram: boolean;
  deadlines: boolean;
  grades: boolean;
}

interface NotificationsTabProps {
  notifications: NotificationsState;
  setNotifications: (n: NotificationsState) => void;
  isVkLinked: boolean;
  isTelegramLinked: boolean;
}

export function NotificationsTab({ }: NotificationsTabProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.2 }}
    >
      <CardSpotlight className="p-8">
        <h3 className="text-lg font-semibold text-foreground mb-6">Уведомления</h3>
        
        {/* В разработке */}
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="p-4 rounded-full bg-amber-500/10 border border-amber-500/20 mb-4">
            <IconTool className="h-10 w-10 text-amber-500" />
          </div>
          <h4 className="text-lg font-medium text-foreground mb-2">В разработке...</h4>
          <p className="text-sm text-muted-foreground max-w-sm">
            Настройка уведомлений скоро будет доступна. Мы работаем над этим функционалом.
          </p>
        </div>

        {/* Превью функционала (неактивное) */}
        <div className="mt-6 opacity-40 pointer-events-none select-none">
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-muted-foreground">Каналы уведомлений</h4>
            <NotificationItemPreview
              icon={<IconBrandVk className="h-6 w-6 text-blue-600" />}
              title="ВКонтакте уведомления"
              description="Получать уведомления в ВК"
            />
            <NotificationItemPreview
              icon={<IconBrandTelegram className="h-6 w-6 text-blue-400" />}
              title="Telegram уведомления"
              description="Получать уведомления в Telegram"
            />
          </div>
          <div className="space-y-4 mt-6">
            <h4 className="text-sm font-medium text-muted-foreground">Типы уведомлений</h4>
            <NotificationItemPreview
              icon={<IconClock className="h-6 w-6 text-yellow-500" />}
              title="Дедлайны"
              description="Напоминания о приближающихся дедлайнах"
            />
            <NotificationItemPreview
              icon={<IconStar className="h-6 w-6 text-green-500" />}
              title="Оценки"
              description="Уведомления о новых оценках"
            />
          </div>
        </div>
      </CardSpotlight>
    </motion.div>
  );
}

function NotificationItemPreview({ icon, title, description }: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className={cn(
      "flex items-start gap-4 p-4 rounded-lg border",
      "bg-neutral-100 dark:bg-neutral-900/30 border-neutral-200 dark:border-neutral-800"
    )}>
      <div className="p-2 rounded-lg border bg-neutral-200 dark:bg-neutral-800 border-neutral-300 dark:border-neutral-700">
        {icon}
      </div>
      <div className="flex-1">
        <h4 className="font-medium text-foreground mb-1">{title}</h4>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="w-11 h-6 rounded-full bg-neutral-300 dark:bg-neutral-700" />
    </div>
  );
}
