'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { StudentAPI, StudentProfile, RelinkTelegramResponse } from '@/lib/api';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { TextGenerateEffect } from '@/components/ui/text-generate-effect';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  IconUser, 
  IconBell, 
  IconPalette, 
  IconShield,
  IconBrandVk,
  IconBrandTelegram,
  IconClock,
  IconStar,
  IconCheck,
  IconAlertCircle,
  IconLink,
  IconLinkOff,
  IconRefresh,
  IconCopy,
  IconExternalLink,
} from '@tabler/icons-react';
import { useTheme } from 'next-themes';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const { theme, setTheme } = useTheme();
  const [notifications, setNotifications] = useState({
    vk: false,
    telegram: true,
    deadlines: true,
    grades: true,
  });

  // Relink Telegram state
  const [relinkDialogOpen, setRelinkDialogOpen] = useState(false);
  const [relinkData, setRelinkData] = useState<RelinkTelegramResponse | null>(null);
  const [relinkLoading, setRelinkLoading] = useState(false);

  // Заглушка: ВК не привязан
  const isVkLinked = false;
  const isTelegramLinked = !!profile?.username;

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

  const copyCode = () => {
    if (relinkData?.code) {
      navigator.clipboard.writeText(relinkData.code);
      toast.success('Код скопирован');
    }
  };

  if (loading) return <SettingsSkeleton />;

  const initials = profile?.full_name?.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() || 'СТ';

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="space-y-2">
        <TextGenerateEffect words="Настройки" className="text-2xl font-bold" duration={0.3} />
        <p className="text-muted-foreground">Управление профилем и предпочтениями</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 bg-neutral-100 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 p-1">
          <TabsTrigger value="profile" className="gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-800">
            <IconUser className="h-4 w-4" />
            <span className="hidden sm:inline">Профиль</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-800">
            <IconBell className="h-4 w-4" />
            <span className="hidden sm:inline">Уведомления</span>
          </TabsTrigger>
          <TabsTrigger value="appearance" className="gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-800">
            <IconPalette className="h-4 w-4" />
            <span className="hidden sm:inline">Тема</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-800">
            <IconShield className="h-4 w-4" />
            <span className="hidden sm:inline">Безопасность</span>
          </TabsTrigger>
        </TabsList>

        <AnimatePresence mode="wait">
          <TabsContent value="profile" key="profile-tab">
            <motion.div key="profile-content" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.2 }}>
              <CardSpotlight className="p-8">
                <div className="flex items-start gap-6 mb-8">
                  <Avatar className="h-24 w-24 border-2 border-primary/20">
                    <AvatarFallback className="text-3xl bg-gradient-to-br from-primary/20 to-primary/5 text-primary">{initials}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-foreground mb-1">{profile?.full_name}</h3>
                    <p className="text-muted-foreground mb-4">@{profile?.username || 'student'}</p>
                    <div className="flex gap-2">
                      <div className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs text-primary">
                        {profile?.role === 'student' ? 'Студент' : profile?.role}
                      </div>
                      {profile?.group?.code && (
                        <div className="px-3 py-1 rounded-full bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-xs text-neutral-600 dark:text-neutral-300">
                          {profile.group.code}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <Separator className="bg-neutral-200 dark:bg-neutral-800 mb-6" />
                <div className="grid gap-4">
                  <ProfileField label="ФИО" value={profile?.full_name || ''} icon={<IconUser className="h-4 w-4" />} />
                  <div className="grid md:grid-cols-2 gap-4">
                    <ProfileField label="Username" value={profile?.username || '—'} icon={<IconBrandTelegram className="h-4 w-4" />} />
                    <ProfileField label="Группа" value={profile?.group?.code || '—'} icon={<IconUser className="h-4 w-4" />} />
                  </div>
                </div>
              </CardSpotlight>
            </motion.div>
          </TabsContent>

          <TabsContent value="notifications" key="notifications-tab">
            <motion.div key="notifications-content" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.2 }}>
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
          </TabsContent>

          <TabsContent value="appearance" key="appearance-tab">
            <motion.div key="appearance-content" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.2 }}>
              <CardSpotlight className="p-8">
                <h3 className="text-lg font-semibold text-foreground mb-6">Тема оформления</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <ThemeCard active={theme === 'light'} onClick={() => setTheme('light')} title="Светлая" description="Классическая светлая тема"
                    preview={<div className="h-20 rounded-lg bg-white border-2 border-neutral-300 p-2 space-y-1"><div className="h-2 bg-neutral-200 rounded w-3/4" /><div className="h-2 bg-neutral-300 rounded w-1/2" /></div>} />
                  <ThemeCard active={theme === 'dark'} onClick={() => setTheme('dark')} title="Тёмная" description="Современная тёмная тема"
                    preview={<div className="h-20 rounded-lg bg-neutral-900 border-2 border-neutral-700 p-2 space-y-1"><div className="h-2 bg-neutral-700 rounded w-3/4" /><div className="h-2 bg-neutral-600 rounded w-1/2" /></div>} />
                  <ThemeCard active={theme === 'system'} onClick={() => setTheme('system')} title="Системная" description="Следует системным настройкам"
                    preview={<div className="h-20 rounded-lg bg-gradient-to-r from-white via-neutral-500 to-neutral-900 border-2 border-neutral-500 p-2 space-y-1"><div className="h-2 bg-neutral-400 rounded w-3/4" /><div className="h-2 bg-neutral-500 rounded w-1/2" /></div>} />
                </div>
              </CardSpotlight>
            </motion.div>
          </TabsContent>

          <TabsContent value="security" key="security-tab">
            <motion.div key="security-content" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.2 }}>
              <CardSpotlight className="p-8">
                <h3 className="text-lg font-semibold text-foreground mb-6">Привязанные аккаунты</h3>
                <div className="space-y-4">
                  {/* Telegram */}
                  <div className="flex items-start gap-4 p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800">
                    <div className={cn("p-3 rounded-lg", isTelegramLinked ? "bg-green-500/10" : "bg-neutral-500/10")}>
                      <IconBrandTelegram className={cn("h-6 w-6", isTelegramLinked ? "text-blue-400" : "text-neutral-400")} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-foreground">Telegram</h4>
                        {isTelegramLinked ? (
                          <span className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-600 dark:text-green-400 text-xs flex items-center gap-1">
                            <IconCheck className="h-3 w-3" /> Привязан
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full bg-neutral-500/10 text-neutral-500 text-xs flex items-center gap-1">
                            <IconLinkOff className="h-3 w-3" /> Не привязан
                          </span>
                        )}
                      </div>
                      {isTelegramLinked ? (
                        <p className="text-sm text-muted-foreground">
                          Username: <span className="font-medium text-primary">@{profile?.username}</span>
                        </p>
                      ) : (
                        <p className="text-sm text-muted-foreground">Привяжите Telegram для авторизации и уведомлений</p>
                      )}
                    </div>
                    {isTelegramLinked ? (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="gap-2"
                        onClick={handleRelinkTelegram}
                        disabled={relinkLoading}
                      >
                        <IconRefresh className={cn("h-4 w-4", relinkLoading && "animate-spin")} /> 
                        Перепривязать
                      </Button>
                    ) : (
                      <Button variant="outline" size="sm" className="gap-2">
                        <IconLink className="h-4 w-4" /> Привязать
                      </Button>
                    )}
                  </div>

                  {/* VK */}
                  <div className="flex items-start gap-4 p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800">
                    <div className={cn("p-3 rounded-lg", isVkLinked ? "bg-green-500/10" : "bg-neutral-500/10")}>
                      <IconBrandVk className={cn("h-6 w-6", isVkLinked ? "text-blue-600" : "text-neutral-400")} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-foreground">ВКонтакте</h4>
                        {isVkLinked ? (
                          <span className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-600 dark:text-green-400 text-xs flex items-center gap-1">
                            <IconCheck className="h-3 w-3" /> Привязан
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full bg-neutral-500/10 text-neutral-500 text-xs flex items-center gap-1">
                            <IconLinkOff className="h-3 w-3" /> Не привязан
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {isVkLinked ? "Аккаунт ВК привязан" : "Привяжите ВК для получения уведомлений"}
                      </p>
                    </div>
                    <Button variant="outline" size="sm" className="gap-2" disabled>
                      <IconLink className="h-4 w-4" /> Скоро
                    </Button>
                  </div>
                </div>

                <Separator className="bg-neutral-200 dark:bg-neutral-800 my-6" />

                <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                  <div className="flex items-start gap-4">
                    <div className="p-2 rounded-lg bg-yellow-500/10">
                      <IconAlertCircle className="h-5 w-5 text-yellow-500" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-yellow-600 dark:text-yellow-500 mb-1">Смена пароля недоступна</h4>
                      <p className="text-sm text-muted-foreground">Авторизация осуществляется через мессенджеры. Для смены аккаунта выйдите и войдите заново.</p>
                    </div>
                  </div>
                </div>
              </CardSpotlight>

              {/* Relink Telegram Dialog */}
              <Dialog open={relinkDialogOpen} onOpenChange={setRelinkDialogOpen}>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                      <IconBrandTelegram className="h-5 w-5 text-blue-400" />
                      Перепривязка Telegram
                    </DialogTitle>
                    <DialogDescription>
                      Отправьте команду боту с нового Telegram аккаунта
                    </DialogDescription>
                  </DialogHeader>
                  
                  {relinkData && (
                    <div className="space-y-4">
                      <div className="p-4 rounded-lg bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
                        <Label className="text-xs text-muted-foreground mb-2 block">Ваш код</Label>
                        <div className="flex items-center gap-2">
                          <code className="flex-1 text-2xl font-mono font-bold tracking-wider text-primary">
                            {relinkData.code}
                          </code>
                          <Button variant="ghost" size="icon" onClick={copyCode}>
                            <IconCopy className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      <div className="text-sm text-muted-foreground space-y-2">
                        <p>1. Откройте бота в Telegram</p>
                        <p>2. Отправьте команду: <code className="px-1 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800">/start {relinkData.code}</code></p>
                        <p>3. Старая привязка будет заменена</p>
                      </div>

                      <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
                        <IconClock className="h-4 w-4" />
                        <span>Код действует {Math.floor(relinkData.expires_in / 60)} минут</span>
                      </div>

                      {process.env.NEXT_PUBLIC_BOT_URL && (
                        <Button asChild className="w-full gap-2">
                          <a href={`${process.env.NEXT_PUBLIC_BOT_URL}?start=${relinkData.code}`} target="_blank" rel="noopener noreferrer">
                            <IconExternalLink className="h-4 w-4" />
                            Открыть бота
                          </a>
                        </Button>
                      )}
                    </div>
                  )}
                </DialogContent>
              </Dialog>
            </motion.div>
          </TabsContent>
        </AnimatePresence>
      </Tabs>
    </div>
  );
}

function ProfileField({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800">
      <div className="flex items-center gap-2 mb-2">
        <div className="text-neutral-500 dark:text-neutral-400">{icon}</div>
        <Label className="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">{label}</Label>
      </div>
      <p className="text-foreground font-medium">{value}</p>
    </div>
  );
}

function ThemeCard({ active, onClick, title, description, preview }: { active: boolean; onClick: () => void; title: string; description: string; preview: React.ReactNode }) {
  return (
    <button onClick={onClick} className={cn("p-4 rounded-xl border-2 transition-all text-left", active ? "border-primary bg-primary/5 shadow-lg shadow-primary/20" : "border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-900/50")}>
      <div className="mb-3">{preview}</div>
      <h4 className="font-semibold text-foreground mb-1">{title}</h4>
      <p className="text-xs text-muted-foreground">{description}</p>
      {active && <div className="mt-3 flex items-center gap-1 text-xs text-primary"><IconCheck className="h-3 w-3" /><span>Активна</span></div>}
    </button>
  );
}

function NotificationItem({ icon, title, description, checked, onCheckedChange, disabled }: { icon: React.ReactNode; title: string; description: string; checked: boolean; onCheckedChange: (c: boolean) => void; disabled?: boolean }) {
  return (
    <div className={cn("flex items-start gap-4 p-4 rounded-lg border", disabled ? "bg-neutral-100 dark:bg-neutral-900/30 border-neutral-200 dark:border-neutral-800 opacity-60" : "bg-neutral-50 dark:bg-neutral-900/50 border-neutral-200 dark:border-neutral-800")}>
      <div className={cn("p-2 rounded-lg border", disabled ? "bg-neutral-200 dark:bg-neutral-800 border-neutral-300 dark:border-neutral-700" : "bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-800")}>{icon}</div>
      <div className="flex-1">
        <h4 className="font-medium text-foreground mb-1">{title}</h4>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} disabled={disabled} />
    </div>
  );
}

function SettingsSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div className="space-y-2"><Skeleton className="h-8 w-32" /><Skeleton className="h-4 w-48" /></div>
      <Skeleton className="h-12 w-full max-w-md" />
      <Skeleton className="h-[400px] rounded-xl" />
    </div>
  );
}
