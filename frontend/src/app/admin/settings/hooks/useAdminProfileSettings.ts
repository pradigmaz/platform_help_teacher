'use client';

import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { AdminAPI, ContactVisibility, type LinkVkResponse, type RelinkTelegramResponse } from '@/lib/api';
import type { AdminProfile } from '@/lib/api/admin';
import type { ContactFieldKey } from '../components';

export function useAdminProfileSettings() {
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
  const [relinkDialogOpen, setRelinkDialogOpen] = useState(false);
  const [relinkData, setRelinkData] = useState<RelinkTelegramResponse | null>(null);
  const [relinkLoading, setRelinkLoading] = useState(false);
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

    void loadData();
  }, []);

  const handleRelinkTelegram = useCallback(async () => {
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
  }, []);

  const handleLinkVk = useCallback(async () => {
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
  }, []);

  const handleContactChange = useCallback((key: ContactFieldKey, value: string) => {
    setContacts((current) => ({ ...current, [key]: value }));
  }, []);

  const handleVisibilityChange = useCallback((key: ContactFieldKey, value: ContactVisibility) => {
    setVisibility((current) => ({ ...current, [key]: value }));
  }, []);

  const handleSave = useCallback(async () => {
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
  }, [contacts, visibility]);

  return {
    isLoading,
    isSaving,
    profile,
    contacts,
    visibility,
    relinkDialogOpen,
    relinkData,
    relinkLoading,
    vkDialogOpen,
    vkData,
    vkLoading,
    setRelinkDialogOpen,
    setVkDialogOpen,
    handleRelinkTelegram,
    handleLinkVk,
    handleContactChange,
    handleVisibilityChange,
    handleSave,
  };
}
