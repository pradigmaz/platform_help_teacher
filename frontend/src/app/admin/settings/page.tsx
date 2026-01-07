'use client';

import { useEffect, useState } from 'react';
import { 
  Save, 
  Loader2,
  Eye,
  EyeOff,
  Users,
  FileText,
  Settings2,
  MessageSquare,
  RefreshCw,
  Copy,
  ExternalLink,
  Clock,
} from 'lucide-react';
import { 
  IconBrandTelegram, 
  IconBrandVk,
  IconMessage,
} from '@tabler/icons-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { AdminAPI, ContactVisibility, RelinkTelegramResponse, LinkVkResponse } from '@/lib/api';
import type { AdminProfile } from '@/lib/api/admin';
import { cn } from '@/lib/utils';

const visibilityOptions: { value: ContactVisibility; label: string; icon: React.ReactNode; description: string }[] = [
  { value: 'student', label: 'Студентам', icon: <Users className="h-4 w-4" />, description: 'Видно в ЛК студента' },
  { value: 'report', label: 'В отчёте', icon: <FileText className="h-4 w-4" />, description: 'Видно в публичном отчёте' },
  { value: 'both', label: 'Везде', icon: <Eye className="h-4 w-4" />, description: 'Видно везде' },
  { value: 'none', label: 'Скрыто', icon: <EyeOff className="h-4 w-4" />, description: 'Не отображается' },
];

const contactFields = [
  { 
    key: 'telegram', 
    label: 'Telegram', 
    icon: IconBrandTelegram, 
    placeholder: '@username',
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    description: 'Ваш Telegram для связи'
  },
  { 
    key: 'vk', 
    label: 'ВКонтакте', 
    icon: IconBrandVk, 
    placeholder: 'vk.com/id или @username',
    color: 'text-blue-600',
    bgColor: 'bg-blue-600/10',
    description: 'Страница или группа ВК'
  },
  { 
    key: 'max', 
    label: 'MAX', 
    icon: IconMessage, 
    placeholder: '@username или ссылка',
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    description: 'Мессенджер MAX'
  },
] as const;

type ContactFieldKey = typeof contactFields[number]['key'];

export default function AdminSettingsPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [profile, setProfile] = useState<AdminProfile | null>(null);
  const [contacts, setContacts] = useState<Record<ContactFieldKey, string>>({
    telegram: '',
    vk: '',
    max: '',
  });
  const [visibility, setVisibility] = useState<Record<ContactFieldKey, ContactVisibility>>({
    telegram: 'none',
    vk: 'none',
    max: 'none',
  });

  // Relink Telegram state
  const [relinkDialogOpen, setRelinkDialogOpen] = useState(false);
  const [relinkData, setRelinkData] = useState<RelinkTelegramResponse | null>(null);
  const [relinkLoading, setRelinkLoading] = useState(false);

  // Link VK state
  const [vkDialogOpen, setVkDialogOpen] = useState(false);
  const [vkData, setVkData] = useState<LinkVkResponse | null>(null);
  const [vkLoading, setVkLoading] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [profileData, contactsData] = await Promise.all([
          AdminAPI.getProfile(),
          AdminAPI.getContacts(),
        ]);
        setProfile(profileData);
        setContacts({
          telegram: contactsData.contacts.telegram || '',
          vk: contactsData.contacts.vk || '',
          max: contactsData.contacts.max || '',
        });
        setVisibility({
          telegram: contactsData.visibility.telegram || 'none',
          vk: contactsData.visibility.vk || 'none',
          max: contactsData.visibility.max || 'none',
        });
      } catch (error) {
        console.error('Failed to load data:', error);
        toast.error('Ошибка загрузки данных');
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, []);

  const handleRelinkTelegram = async () => {
    setRelinkLoading(true);
    try {
      const data = await AdminAPI.relinkTelegram();
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

  const handleLinkVk = async () => {
    setVkLoading(true);
    try {
      const data = await AdminAPI.linkVk();
      setVkData(data);
      setVkDialogOpen(true);
    } catch {
      toast.error('Ошибка получения кода привязки ВК');
    } finally {
      setVkLoading(false);
    }
  };

  const copyVkCode = () => {
    if (vkData?.code) {
      navigator.clipboard.writeText(vkData.code);
      toast.success('Код скопирован');
    }
  };

  const handleContactChange = (key: ContactFieldKey, value: string) => {
    setContacts(prev => ({ ...prev, [key]: value }));
  };

  const handleVisibilityChange = (key: ContactFieldKey, value: ContactVisibility) => {
    setVisibility(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await AdminAPI.updateContacts({
        contacts,
        visibility,
      });
      toast.success('Контакты сохранены');
    } catch (error) {
      console.error('Failed to save contacts:', error);
      const message = error instanceof Error ? error.message : 'Ошибка сохранения контактов';
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  const getVisibilityBadge = (vis: ContactVisibility) => {
    const option = visibilityOptions.find(o => o.value === vis);
    if (!option || vis === 'none') return null;
    
    return (
      <Badge variant="secondary" className="text-xs gap-1">
        {option.icon}
        {option.label}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Загрузка настроек...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      {/* Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Settings2 className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Настройки</h1>
            <p className="text-muted-foreground">Управление контактной информацией</p>
          </div>
        </div>
      </div>

      {/* Contacts Card */}
      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <MessageSquare className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <CardTitle className="text-lg">Контакты для связи</CardTitle>
              <CardDescription>
                Укажите мессенджеры, через которые студенты смогут с вами связаться
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {contactFields.map((field, index) => (
            <div key={field.key}>
              {index > 0 && <Separator className="mb-6" />}
              
              <div className="space-y-4">
                {/* Field Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn("p-2 rounded-lg", field.bgColor)}>
                      <field.icon className={cn("h-5 w-5", field.color)} />
                    </div>
                    <div>
                      <Label className="text-base font-medium">{field.label}</Label>
                      <p className="text-xs text-muted-foreground">{field.description}</p>
                    </div>
                  </div>
                  {getVisibilityBadge(visibility[field.key])}
                </div>

                {/* Input and Visibility */}
                <div className="grid gap-4 sm:grid-cols-[1fr,180px]">
                  <div className="relative">
                    <Input
                      id={field.key}
                      placeholder={field.placeholder}
                      value={contacts[field.key]}
                      onChange={(e) => handleContactChange(field.key, e.target.value)}
                      className="h-11"
                    />
                  </div>
                  
                  <Select
                    value={visibility[field.key]}
                    onValueChange={(value) => handleVisibilityChange(field.key, value as ContactVisibility)}
                  >
                    <SelectTrigger className="h-11">
                      <SelectValue placeholder="Видимость" />
                    </SelectTrigger>
                    <SelectContent>
                      {visibilityOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          <div className="flex items-center gap-2">
                            {option.icon}
                            <div className="flex flex-col">
                              <span>{option.label}</span>
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          ))}

          {/* Save Button */}
          <div className="flex justify-end pt-4 border-t">
            <Button 
              onClick={handleSave} 
              disabled={isSaving}
              size="lg"
              className="min-w-[140px]"
            >
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Сохранение...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Сохранить
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="border-dashed bg-muted/30">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="p-2 rounded-lg bg-amber-500/10 h-fit">
              <Eye className="h-5 w-5 text-amber-500" />
            </div>
            <div className="space-y-2">
              <h3 className="font-medium">Как работает видимость?</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li className="flex items-center gap-2">
                  <Users className="h-3.5 w-3.5" />
                  <span><strong>Студентам</strong> — контакт виден в личном кабинете студента</span>
                </li>
                <li className="flex items-center gap-2">
                  <FileText className="h-3.5 w-3.5" />
                  <span><strong>В отчёте</strong> — контакт виден в публичном отчёте для родителей</span>
                </li>
                <li className="flex items-center gap-2">
                  <Eye className="h-3.5 w-3.5" />
                  <span><strong>Везде</strong> — контакт виден и студентам, и в отчёте</span>
                </li>
                <li className="flex items-center gap-2">
                  <EyeOff className="h-3.5 w-3.5" />
                  <span><strong>Скрыто</strong> — контакт нигде не отображается</span>
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Telegram Account Card */}
      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <IconBrandTelegram className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <CardTitle className="text-lg">Telegram аккаунт</CardTitle>
              <CardDescription>
                Управление привязкой Telegram для авторизации
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center gap-3">
              <div className={cn("p-2 rounded-lg", profile?.telegram_id ? "bg-green-500/10" : "bg-neutral-500/10")}>
                <IconBrandTelegram className={cn("h-5 w-5", profile?.telegram_id ? "text-blue-400" : "text-neutral-400")} />
              </div>
              <div>
                <p className="font-medium">{profile?.telegram_id ? 'Telegram привязан' : 'Telegram не привязан'}</p>
                <p className="text-sm text-muted-foreground">
                  {profile?.telegram_id 
                    ? (profile?.username ? `@${profile.username}` : `ID: ${profile.telegram_id}`)
                    : 'Привяжите для входа в систему'}
                </p>
              </div>
            </div>
            <Button 
              variant="outline" 
              onClick={handleRelinkTelegram}
              disabled={relinkLoading}
              className="gap-2"
            >
              <RefreshCw className={cn("h-4 w-4", relinkLoading && "animate-spin")} />
              Перепривязать
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* VK Account Card */}
      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-600/10">
              <IconBrandVk className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <CardTitle className="text-lg">ВКонтакте аккаунт</CardTitle>
              <CardDescription>
                Привязка ВК для уведомлений
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800">
            <div className="flex items-center gap-3">
              <div className={cn("p-2 rounded-lg", profile?.vk_id ? "bg-green-500/10" : "bg-neutral-500/10")}>
                <IconBrandVk className={cn("h-5 w-5", profile?.vk_id ? "text-blue-600" : "text-neutral-400")} />
              </div>
              <div>
                <p className="font-medium">{profile?.vk_id ? 'ВКонтакте привязан' : 'ВКонтакте не привязан'}</p>
                <p className="text-sm text-muted-foreground">
                  {profile?.vk_id ? `ID: ${profile.vk_id}` : 'Для получения уведомлений в ВК'}
                </p>
              </div>
            </div>
            <Button 
              variant="outline" 
              onClick={handleLinkVk}
              disabled={vkLoading}
              className="gap-2"
            >
              <RefreshCw className={cn("h-4 w-4", vkLoading && "animate-spin")} />
              {profile?.vk_id ? 'Перепривязать' : 'Привязать'}
            </Button>
          </div>
        </CardContent>
      </Card>

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
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="text-sm text-muted-foreground space-y-2">
                <p>1. Откройте бота в Telegram</p>
                <p>2. Отправьте команду: <code className="px-1 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800">/start {relinkData.code}</code></p>
                <p>3. Старая привязка будет заменена</p>
              </div>

              <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
                <Clock className="h-4 w-4" />
                <span>Код действует {Math.floor(relinkData.expires_in / 60)} минут</span>
              </div>

              {process.env.NEXT_PUBLIC_BOT_URL && (
                <Button asChild className="w-full gap-2">
                  <a href={`${process.env.NEXT_PUBLIC_BOT_URL}?start=${relinkData.code}`} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4" />
                    Открыть бота
                  </a>
                </Button>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Link VK Dialog */}
      <Dialog open={vkDialogOpen} onOpenChange={setVkDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <IconBrandVk className="h-5 w-5 text-blue-600" />
              Привязка ВКонтакте
            </DialogTitle>
            <DialogDescription>
              Отправьте команду боту в ВК
            </DialogDescription>
          </DialogHeader>
          
          {vkData && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
                <Label className="text-xs text-muted-foreground mb-2 block">Ваш код</Label>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-2xl font-mono font-bold tracking-wider text-primary">
                    {vkData.code}
                  </code>
                  <Button variant="ghost" size="icon" onClick={copyVkCode}>
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="text-sm text-muted-foreground space-y-2">
                <p>1. Откройте бота в ВКонтакте</p>
                <p>2. Отправьте сообщение: <code className="px-1 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800">/start {vkData.code}</code></p>
                <p>3. Аккаунт будет привязан</p>
              </div>

              <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
                <Clock className="h-4 w-4" />
                <span>Код действует {Math.floor(vkData.expires_in / 60)} минут</span>
              </div>

              {process.env.NEXT_PUBLIC_VK_BOT_URL && (
                <Button asChild className="w-full gap-2">
                  <a href={process.env.NEXT_PUBLIC_VK_BOT_URL} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4" />
                    Открыть бота ВК
                  </a>
                </Button>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
