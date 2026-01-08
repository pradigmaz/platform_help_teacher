'use client';

import { useEffect, useState } from 'react';
import { Loader2, Settings2 } from 'lucide-react';
import { toast } from 'sonner';
import { AdminAPI, ContactVisibility, RelinkTelegramResponse, LinkVkResponse } from '@/lib/api';
import type { AdminProfile } from '@/lib/api/admin';
import {
  ContactsCard,
  TelegramCard,
  VkCard,
  VisibilityInfoCard,
  type ContactFieldKey,
} from './components';

export default function AdminSettingsPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [profile, setProfile] = useState<AdminProfile | null>(null);
  const [contacts, setContacts] = useState<Record<ContactFieldKey, string>>({
    telegram: '', vk: '', max: '',
  });
  const [visibility, setVisibility] = useState<Record<ContactFieldKey, ContactVisibility>>({
    telegram: 'none', vk: 'none', max: 'none',
  });

  // Telegram relink state
  const [relinkDialogOpen, setRelinkDialogOpen] = useState(false);
  const [relinkData, setRelinkData] = useState<RelinkTelegramResponse | null>(null);
  const [relinkLoading, setRelinkLoading] = useState(false);

  // VK link state
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

  const handleContactChange = (key: ContactFieldKey, value: string) => {
    setContacts(prev => ({ ...prev, [key]: value }));
  };

  const handleVisibilityChange = (key: ContactFieldKey, value: ContactVisibility) => {
    setVisibility(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await AdminAPI.updateContacts({ contacts, visibility });
      toast.success('Контакты сохранены');
    } catch (error) {
      console.error('Failed to save contacts:', error);
      toast.error(error instanceof Error ? error.message : 'Ошибка сохранения контактов');
    } finally {
      setIsSaving(false);
    }
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

      <ContactsCard
        contacts={contacts}
        visibility={visibility}
        isSaving={isSaving}
        onContactChange={handleContactChange}
        onVisibilityChange={handleVisibilityChange}
        onSave={handleSave}
      />

      <VisibilityInfoCard />

      <TelegramCard
        profile={profile}
        relinkData={relinkData}
        relinkDialogOpen={relinkDialogOpen}
        relinkLoading={relinkLoading}
        onRelink={handleRelinkTelegram}
        onDialogChange={setRelinkDialogOpen}
      />

      <VkCard
        profile={profile}
        vkData={vkData}
        vkDialogOpen={vkDialogOpen}
        vkLoading={vkLoading}
        onLink={handleLinkVk}
        onDialogChange={setVkDialogOpen}
      />
    </div>
  );
}
