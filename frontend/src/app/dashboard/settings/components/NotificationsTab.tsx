'use client';

import { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { IconBrandVk, IconBrandTelegram, IconClock, IconStar, IconBell, IconTool, IconWorld } from '@tabler/icons-react';
import { Loader2 } from 'lucide-react';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import { api } from '@/lib/api';

interface NotificationSettings {
  channel_telegram: boolean;
  channel_vk: boolean;
  channel_web: boolean;
  notify_announcements: boolean;
}

interface NotificationsTabProps {
  notifications: { vk: boolean; telegram: boolean; deadlines: boolean; grades: boolean };
  setNotifications: (n: { vk: boolean; telegram: boolean; deadlines: boolean; grades: boolean }) => void;
  isVkLinked: boolean;
  isTelegramLinked: boolean;
}

export function NotificationsTab({ isVkLinked, isTelegramLinked }: NotificationsTabProps) {
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const { data } = await api.get<NotificationSettings>('/student/notifications/settings');
      setSettings(data);
    } catch {
      toast.error('Ошибка загрузки настроек');
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = async (key: keyof NotificationSettings, value: boolean) => {
    if (!settings) return;
    
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    setSaving(true);
    
    try {
      await api.put('/student/notifications/settings', newSettings);
    } catch {
      setSettings(settings); // rollback
      toast.error('Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <CardSpotlight className="p-8 flex items-center justify-center min-h-[300px]">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardSpotlight>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.2 }}
    >
      <CardSpotlight className="p-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-foreground">Уведомления</h3>
          {saving && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
        </div>
        
        {/* Каналы */}
        <div className="space-y-4 mb-8">
          <h4 className="text-sm font-medium text-muted-foreground">Каналы уведомлений</h4>
          
          <NotificationItem
            icon={<IconWorld className="h-5 w-5 text-green-500" />}
            title="На сайте"
            description="Уведомления в личном кабинете"
            checked={settings?.channel_web ?? true}
            onChange={(v) => updateSetting('channel_web', v)}
          />
          
          <NotificationItem
            icon={<IconBrandTelegram className="h-5 w-5 text-blue-400" />}
            title="Telegram"
            description={isTelegramLinked ? "Получать уведомления в Telegram" : "Привяжите Telegram в разделе Безопасность"}
            checked={settings?.channel_telegram ?? false}
            onChange={(v) => updateSetting('channel_telegram', v)}
            disabled={!isTelegramLinked}
          />
          
          <NotificationItem
            icon={<IconBrandVk className="h-5 w-5 text-blue-600" />}
            title="ВКонтакте"
            description={isVkLinked ? "Получать уведомления в ВК" : "Привяжите ВК в разделе Безопасность"}
            checked={settings?.channel_vk ?? false}
            onChange={(v) => updateSetting('channel_vk', v)}
            disabled={!isVkLinked}
          />
        </div>

        {/* Типы */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground">Типы уведомлений</h4>
          
          <NotificationItem
            icon={<IconBell className="h-5 w-5 text-purple-500" />}
            title="Объявления"
            description="Новости и обновления системы"
            checked={settings?.notify_announcements ?? true}
            onChange={(v) => updateSetting('notify_announcements', v)}
          />
          
          {/* Заглушки */}
          <NotificationItemDisabled
            icon={<IconClock className="h-5 w-5 text-yellow-500" />}
            title="Дедлайны"
            description="Напоминания о приближающихся дедлайнах"
          />
          
          <NotificationItemDisabled
            icon={<IconStar className="h-5 w-5 text-green-500" />}
            title="Оценки"
            description="Уведомления о новых оценках"
          />
        </div>
      </CardSpotlight>
    </motion.div>
  );
}

function NotificationItem({ icon, title, description, checked, onChange, disabled }: {
  icon: React.ReactNode;
  title: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <div className={cn(
      "flex items-center gap-4 p-4 rounded-lg border transition-colors",
      disabled 
        ? "bg-neutral-100/50 dark:bg-neutral-900/20 border-neutral-200/50 dark:border-neutral-800/50 opacity-60" 
        : "bg-neutral-100 dark:bg-neutral-900/30 border-neutral-200 dark:border-neutral-800"
    )}>
      <div className={cn(
        "p-2 rounded-lg border",
        disabled 
          ? "bg-neutral-200/50 dark:bg-neutral-800/50 border-neutral-300/50 dark:border-neutral-700/50"
          : "bg-neutral-200 dark:bg-neutral-800 border-neutral-300 dark:border-neutral-700"
      )}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-foreground">{title}</h4>
        <p className="text-sm text-muted-foreground truncate">{description}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onChange} disabled={disabled} />
    </div>
  );
}

function NotificationItemDisabled({ icon, title, description }: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-center gap-4 p-4 rounded-lg border bg-neutral-100/30 dark:bg-neutral-900/10 border-neutral-200/30 dark:border-neutral-800/30 opacity-50">
      <div className="p-2 rounded-lg border bg-neutral-200/30 dark:bg-neutral-800/30 border-neutral-300/30 dark:border-neutral-700/30">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="font-medium text-foreground">{title}</h4>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
            <IconTool className="h-3 w-3" />
            Скоро
          </span>
        </div>
        <p className="text-sm text-muted-foreground truncate">{description}</p>
      </div>
      <div className="w-11 h-6 rounded-full bg-neutral-300/50 dark:bg-neutral-700/50" />
    </div>
  );
}
