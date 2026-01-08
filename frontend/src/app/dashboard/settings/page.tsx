'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { StudentAPI, StudentProfile, RelinkTelegramResponse } from '@/lib/api';
import type { LinkVkResponse } from '@/lib/api/types/admin';
import { TextGenerateEffect } from '@/components/ui/text-generate-effect';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { IconUser, IconBell, IconPalette, IconShield } from '@tabler/icons-react';
import { useTheme } from 'next-themes';
import { AnimatePresence } from 'motion/react';
import { ProfileTab, NotificationsTab, AppearanceTab, SecurityTab } from './components';

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const { theme, setTheme } = useTheme();
  const [notifications, setNotifications] = useState({
    vk: false, telegram: true, deadlines: true, grades: true,
  });

  // Telegram relink
  const [relinkDialogOpen, setRelinkDialogOpen] = useState(false);
  const [relinkData, setRelinkData] = useState<RelinkTelegramResponse | null>(null);
  const [relinkLoading, setRelinkLoading] = useState(false);

  // VK link
  const [vkDialogOpen, setVkDialogOpen] = useState(false);
  const [vkData, setVkData] = useState<LinkVkResponse | null>(null);
  const [vkLoading, setVkLoading] = useState(false);

  const isVkLinked = !!profile?.vk_id;
  const isTelegramLinked = !!profile?.telegram_id;

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const data = await StudentAPI.getProfile();
        setProfile(data);
      } catch {
        toast.error('Ошибка загрузки профиля');
      } finally {
        setLoading(false);
      }
    };
    loadProfile();
  }, []);

  const handleRelinkTelegram = async () => {
    setRelinkLoading(true);
    try {
      const data = await StudentAPI.relinkTelegram();
      setRelinkData(data);
      setRelinkDialogOpen(true);
    } catch {
      toast.error('Ошибка получения кода перепривязки');
    } finally {
      setRelinkLoading(false);
    }
  };

  const handleLinkVk = async () => {
    setVkLoading(true);
    try {
      const data = await StudentAPI.linkVk();
      setVkData(data);
      setVkDialogOpen(true);
    } catch {
      toast.error('Ошибка получения кода привязки ВК');
    } finally {
      setVkLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6 max-w-5xl mx-auto">
        <div className="space-y-2"><Skeleton className="h-8 w-32" /><Skeleton className="h-4 w-48" /></div>
        <Skeleton className="h-12 w-full max-w-md" />
        <Skeleton className="h-[400px] rounded-xl" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="space-y-2">
        <TextGenerateEffect words="Настройки" className="text-2xl font-bold" duration={0.3} />
        <p className="text-muted-foreground">Управление профилем и предпочтениями</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 bg-neutral-100 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 p-1">
          <TabsTrigger value="profile" className="gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-800">
            <IconUser className="h-4 w-4" /><span className="hidden sm:inline">Профиль</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-800">
            <IconBell className="h-4 w-4" /><span className="hidden sm:inline">Уведомления</span>
          </TabsTrigger>
          <TabsTrigger value="appearance" className="gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-800">
            <IconPalette className="h-4 w-4" /><span className="hidden sm:inline">Тема</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-800">
            <IconShield className="h-4 w-4" /><span className="hidden sm:inline">Безопасность</span>
          </TabsTrigger>
        </TabsList>

        <AnimatePresence mode="wait">
          <TabsContent value="profile" key="profile-tab">
            <ProfileTab profile={profile} />
          </TabsContent>

          <TabsContent value="notifications" key="notifications-tab">
            <NotificationsTab
              notifications={notifications}
              setNotifications={setNotifications}
              isVkLinked={isVkLinked}
              isTelegramLinked={isTelegramLinked}
            />
          </TabsContent>

          <TabsContent value="appearance" key="appearance-tab">
            <AppearanceTab theme={theme} setTheme={setTheme} />
          </TabsContent>

          <TabsContent value="security" key="security-tab">
            <SecurityTab
              profile={profile}
              relinkDialogOpen={relinkDialogOpen}
              setRelinkDialogOpen={setRelinkDialogOpen}
              relinkData={relinkData}
              relinkLoading={relinkLoading}
              onRelinkTelegram={handleRelinkTelegram}
              vkDialogOpen={vkDialogOpen}
              setVkDialogOpen={setVkDialogOpen}
              vkData={vkData}
              vkLoading={vkLoading}
              onLinkVk={handleLinkVk}
            />
          </TabsContent>
        </AnimatePresence>
      </Tabs>
    </div>
  );
}
