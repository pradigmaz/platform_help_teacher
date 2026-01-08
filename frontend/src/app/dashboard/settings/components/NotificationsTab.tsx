'use client';

import { motion } from 'motion/react';
import { IconBrandVk, IconBrandTelegram, IconClock, IconStar } from '@tabler/icons-react';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
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

export function NotificationsTab({ notifications, setNotifications, isVkLinked, isTelegramLinked }: NotificationsTabProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.2 }}
    >
      <CardSpotlight className="p-8">
        <h3 className="text-lg font-semibold text-foreground mb-6">Уведомления</h3>
        <div className="space-y-6">
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-muted-foreground">Каналы уведомлений</h4>
            <NotificationItem
              icon={<IconBrandVk className="h-6 w-6 text-blue-600" />}
              title="ВКонтакте уведомления"
              description={isVkLinked ? "Получать уведомления в ВК" : "Привяжите ВК в разделе Безопасность"}
              checked={notifications.vk}
              onCheckedChange={(c) => setNotifications({ ...notifications, vk: c })}
              disabled={!isVkLinked}
            />
            <NotificationItem
              icon={<IconBrandTelegram className="h-6 w-6 text-blue-400" />}
              title="Telegram уведомления"
              description={isTelegramLinked ? "Получать уведомления в Telegram" : "Привяжите Telegram в разделе Безопасность"}
              checked={notifications.telegram}
              onCheckedChange={(c) => setNotifications({ ...notifications, telegram: c })}
              disabled={!isTelegramLinked}
            />
          </div>
          <Separator className="bg-neutral-200 dark:bg-neutral-800" />
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-muted-foreground">Типы уведомлений</h4>
            <NotificationItem
              icon={<IconClock className="h-6 w-6 text-yellow-500" />}
              title="Дедлайны"
              description="Напоминания о приближающихся дедлайнах"
              checked={notifications.deadlines}
              onCheckedChange={(c) => setNotifications({ ...notifications, deadlines: c })}
            />
            <NotificationItem
              icon={<IconStar className="h-6 w-6 text-green-500" />}
              title="Оценки"
              description="Уведомления о новых оценках"
              checked={notifications.grades}
              onCheckedChange={(c) => setNotifications({ ...notifications, grades: c })}
            />
          </div>
        </div>
      </CardSpotlight>
    </motion.div>
  );
}

function NotificationItem({ icon, title, description, checked, onCheckedChange, disabled }: {
  icon: React.ReactNode;
  title: string;
  description: string;
  checked: boolean;
  onCheckedChange: (c: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <div className={cn(
      "flex items-start gap-4 p-4 rounded-lg border",
      disabled
        ? "bg-neutral-100 dark:bg-neutral-900/30 border-neutral-200 dark:border-neutral-800 opacity-60"
        : "bg-neutral-50 dark:bg-neutral-900/50 border-neutral-200 dark:border-neutral-800"
    )}>
      <div className={cn(
        "p-2 rounded-lg border",
        disabled
          ? "bg-neutral-200 dark:bg-neutral-800 border-neutral-300 dark:border-neutral-700"
          : "bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800"
      )}>
        {icon}
      </div>
      <div className="flex-1">
        <h4 className="font-medium text-foreground mb-1">{title}</h4>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} disabled={disabled} />
    </div>
  );
}
