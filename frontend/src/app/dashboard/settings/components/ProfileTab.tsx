'use client';

import { motion } from 'motion/react';
import { IconUser, IconBrandTelegram } from '@tabler/icons-react';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import type { StudentProfile } from '@/lib/api';

interface ProfileTabProps {
  profile: StudentProfile | null;
}

export function ProfileTab({ profile }: ProfileTabProps) {
  const initials = profile?.full_name?.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() || 'СТ';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.2 }}
    >
      <CardSpotlight className="p-8">
        <div className="flex items-start gap-6 mb-8">
          <Avatar className="h-24 w-24 border-2 border-primary/20">
            <AvatarFallback className="text-3xl bg-gradient-to-br from-primary/20 to-primary/5 text-primary">
              {initials}
            </AvatarFallback>
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
