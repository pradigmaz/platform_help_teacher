'use client';

import { Loader2, User, Database } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BackupTab,
} from './components';
import { ProfileSettingsTab } from './components/ProfileSettingsTab';
import { SettingsPageHeader } from './components/SettingsPageHeader';
import { StudentSessionResetCard } from './components/StudentSessionResetCard';
import { useAdminProfileSettings } from './hooks/useAdminProfileSettings';
import { useStudentSessionReset } from './hooks/useStudentSessionReset';

export default function AdminSettingsPage() {
  const profileSettings = useAdminProfileSettings();
  const sessionReset = useStudentSessionReset();

  if (profileSettings.isLoading) {
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
      <SettingsPageHeader />

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 bg-neutral-100 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800 p-1">
          <TabsTrigger value="profile" className="gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-800">
            <User className="h-4 w-4" />
            <span>Профиль</span>
          </TabsTrigger>
          <TabsTrigger value="backup" className="gap-2 data-[state=active]:bg-white dark:data-[state=active]:bg-neutral-800">
            <Database className="h-4 w-4" />
            <span>Бэкапы</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          <ProfileSettingsTab
            profile={profileSettings.profile}
            contacts={profileSettings.contacts}
            visibility={profileSettings.visibility}
            isSaving={profileSettings.isSaving}
            relinkData={profileSettings.relinkData}
            relinkDialogOpen={profileSettings.relinkDialogOpen}
            relinkLoading={profileSettings.relinkLoading}
            vkData={profileSettings.vkData}
            vkDialogOpen={profileSettings.vkDialogOpen}
            vkLoading={profileSettings.vkLoading}
            onContactChange={profileSettings.handleContactChange}
            onVisibilityChange={profileSettings.handleVisibilityChange}
            onSave={profileSettings.handleSave}
            onRelink={profileSettings.handleRelinkTelegram}
            onRelinkDialogChange={profileSettings.setRelinkDialogOpen}
            onLinkVk={profileSettings.handleLinkVk}
            onVkDialogChange={profileSettings.setVkDialogOpen}
          />
        </TabsContent>

        <TabsContent value="backup">
          <BackupTab />
          <StudentSessionResetCard
            revokeLoading={sessionReset.revokeLoading}
            onRevoke={sessionReset.handleRevokeAllStudentSessions}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
