'use client';

import { ContactsCard } from './ContactsCard';
import { TelegramCard } from './TelegramCard';
import { VisibilityInfoCard } from './VisibilityInfoCard';
import { VkCard } from './VkCard';
import type { ContactFieldKey } from './ContactsCard';
import type { ContactVisibility, LinkVkResponse, RelinkTelegramResponse } from '@/lib/api';
import type { AdminProfile } from '@/lib/api/admin';

interface ProfileSettingsTabProps {
  profile: AdminProfile | null;
  contacts: Record<ContactFieldKey, string>;
  visibility: Record<ContactFieldKey, ContactVisibility>;
  isSaving: boolean;
  relinkData: RelinkTelegramResponse | null;
  relinkDialogOpen: boolean;
  relinkLoading: boolean;
  vkData: LinkVkResponse | null;
  vkDialogOpen: boolean;
  vkLoading: boolean;
  onContactChange: (key: ContactFieldKey, value: string) => void;
  onVisibilityChange: (key: ContactFieldKey, value: ContactVisibility) => void;
  onSave: () => void;
  onRelink: () => void;
  onRelinkDialogChange: (open: boolean) => void;
  onLinkVk: () => void;
  onVkDialogChange: (open: boolean) => void;
}

export function ProfileSettingsTab({
  profile,
  contacts,
  visibility,
  isSaving,
  relinkData,
  relinkDialogOpen,
  relinkLoading,
  vkData,
  vkDialogOpen,
  vkLoading,
  onContactChange,
  onVisibilityChange,
  onSave,
  onRelink,
  onRelinkDialogChange,
  onLinkVk,
  onVkDialogChange,
}: ProfileSettingsTabProps) {
  return (
    <div className="space-y-6">
      <ContactsCard
        contacts={contacts}
        visibility={visibility}
        isSaving={isSaving}
        onContactChange={onContactChange}
        onVisibilityChange={onVisibilityChange}
        onSave={onSave}
      />

      <VisibilityInfoCard />

      <TelegramCard
        profile={profile}
        relinkData={relinkData}
        relinkDialogOpen={relinkDialogOpen}
        relinkLoading={relinkLoading}
        onRelink={onRelink}
        onDialogChange={onRelinkDialogChange}
      />

      <VkCard
        profile={profile}
        vkData={vkData}
        vkDialogOpen={vkDialogOpen}
        vkLoading={vkLoading}
        onLink={onLinkVk}
        onRefreshCode={onLinkVk}
        onDialogChange={onVkDialogChange}
      />
    </div>
  );
}
