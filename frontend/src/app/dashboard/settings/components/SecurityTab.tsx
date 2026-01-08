'use client';

import { motion } from 'motion/react';
import { toast } from 'sonner';
import {
  IconBrandVk, IconBrandTelegram, IconClock, IconCheck,
  IconAlertCircle, IconLink, IconLinkOff, IconRefresh,
  IconCopy, IconExternalLink,
} from '@tabler/icons-react';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import type { StudentProfile, RelinkTelegramResponse } from '@/lib/api';
import type { LinkVkResponse } from '@/lib/api/types/admin';
import { cn } from '@/lib/utils';

interface SecurityTabProps {
  profile: StudentProfile | null;
  relinkDialogOpen: boolean;
  setRelinkDialogOpen: (open: boolean) => void;
  relinkData: RelinkTelegramResponse | null;
  relinkLoading: boolean;
  onRelinkTelegram: () => void;
  vkDialogOpen: boolean;
  setVkDialogOpen: (open: boolean) => void;
  vkData: LinkVkResponse | null;
  vkLoading: boolean;
  onLinkVk: () => void;
}

export function SecurityTab({
  profile, relinkDialogOpen, setRelinkDialogOpen, relinkData, relinkLoading, onRelinkTelegram,
  vkDialogOpen, setVkDialogOpen, vkData, vkLoading, onLinkVk,
}: SecurityTabProps) {
  const isVkLinked = !!profile?.vk_id;
  const isTelegramLinked = !!profile?.telegram_id;

  const copyCode = () => {
    if (relinkData?.code) {
      navigator.clipboard.writeText(relinkData.code);
      toast.success('Код скопирован');
    }
  };

  const copyVkCode = () => {
    if (vkData?.code) {
      navigator.clipboard.writeText(vkData.code);
      toast.success('Код скопирован');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.2 }}
    >
      <CardSpotlight className="p-8">
        <h3 className="text-lg font-semibold text-foreground mb-6">Привязанные аккаунты</h3>
        <div className="space-y-4">
          {/* Telegram */}
          <AccountCard
            icon={<IconBrandTelegram className={cn("h-6 w-6", isTelegramLinked ? "text-blue-400" : "text-neutral-400")} />}
            title="Telegram"
            isLinked={isTelegramLinked}
            linkedInfo={profile?.username ? `@${profile.username}` : `ID: ${profile?.telegram_id}`}
            unlinkedText="Привяжите Telegram для авторизации и уведомлений"
            onAction={onRelinkTelegram}
            actionLoading={relinkLoading}
            actionLabel={isTelegramLinked ? "Перепривязать" : "Привязать"}
          />

          {/* VK */}
          <AccountCard
            icon={<IconBrandVk className={cn("h-6 w-6", isVkLinked ? "text-blue-600" : "text-neutral-400")} />}
            title="ВКонтакте"
            isLinked={isVkLinked}
            linkedInfo={`ID: ${profile?.vk_id}`}
            unlinkedText="Привяжите ВК для получения уведомлений"
            onAction={onLinkVk}
            actionLoading={vkLoading}
            actionLabel={isVkLinked ? "Перепривязать" : "Привязать"}
          />
        </div>

        <Separator className="bg-neutral-200 dark:bg-neutral-800 my-6" />

        <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <div className="flex items-start gap-4">
            <div className="p-2 rounded-lg bg-yellow-500/10">
              <IconAlertCircle className="h-5 w-5 text-yellow-500" />
            </div>
            <div>
              <h4 className="font-semibold text-yellow-600 dark:text-yellow-500 mb-1">Смена пароля недоступна</h4>
              <p className="text-sm text-muted-foreground">Авторизация осуществляется через мессенджеры.</p>
            </div>
          </div>
        </div>
      </CardSpotlight>

      {/* Telegram Dialog */}
      <LinkDialog
        open={relinkDialogOpen}
        onOpenChange={setRelinkDialogOpen}
        icon={<IconBrandTelegram className="h-5 w-5 text-blue-400" />}
        title="Перепривязка Telegram"
        description="Отправьте команду боту с нового Telegram аккаунта"
        code={relinkData?.code}
        expiresIn={relinkData?.expires_in}
        onCopy={copyCode}
        botUrl={process.env.NEXT_PUBLIC_BOT_URL}
        startParam={relinkData?.code}
      />

      {/* VK Dialog */}
      <LinkDialog
        open={vkDialogOpen}
        onOpenChange={setVkDialogOpen}
        icon={<IconBrandVk className="h-5 w-5 text-blue-600" />}
        title={isVkLinked ? 'Перепривязка ВКонтакте' : 'Привязка ВКонтакте'}
        description="Отправьте команду боту в ВК"
        code={vkData?.code}
        expiresIn={vkData?.expires_in}
        onCopy={copyVkCode}
        botUrl={process.env.NEXT_PUBLIC_VK_BOT_URL}
      />
    </motion.div>
  );
}

function AccountCard({ icon, title, isLinked, linkedInfo, unlinkedText, onAction, actionLoading, actionLabel }: {
  icon: React.ReactNode;
  title: string;
  isLinked: boolean;
  linkedInfo: string;
  unlinkedText: string;
  onAction: () => void;
  actionLoading: boolean;
  actionLabel: string;
}) {
  return (
    <div className="flex items-start gap-4 p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-800">
      <div className={cn("p-3 rounded-lg", isLinked ? "bg-green-500/10" : "bg-neutral-500/10")}>{icon}</div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="font-semibold text-foreground">{title}</h4>
          {isLinked ? (
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
          {isLinked ? <span className="font-medium text-primary">{linkedInfo}</span> : unlinkedText}
        </p>
      </div>
      <Button variant="outline" size="sm" className="gap-2" onClick={onAction} disabled={actionLoading}>
        {isLinked ? <IconRefresh className={cn("h-4 w-4", actionLoading && "animate-spin")} /> : <IconLink className={cn("h-4 w-4", actionLoading && "animate-spin")} />}
        {actionLabel}
      </Button>
    </div>
  );
}

function LinkDialog({ open, onOpenChange, icon, title, description, code, expiresIn, onCopy, botUrl, startParam }: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  icon: React.ReactNode;
  title: string;
  description: string;
  code?: string;
  expiresIn?: number;
  onCopy: () => void;
  botUrl?: string;
  startParam?: string;
}) {
  const fullUrl = startParam ? `${botUrl}?start=${startParam}` : botUrl;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">{icon}{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        {code && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
              <Label className="text-xs text-muted-foreground mb-2 block">Ваш код</Label>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-2xl font-mono font-bold tracking-wider text-primary">{code}</code>
                <Button variant="ghost" size="icon" onClick={onCopy}><IconCopy className="h-4 w-4" /></Button>
              </div>
            </div>
            <div className="text-sm text-muted-foreground space-y-2">
              <p>1. Откройте бота</p>
              <p>2. Отправьте: <code className="px-1 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800">/start {code}</code></p>
            </div>
            {expiresIn && (
              <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
                <IconClock className="h-4 w-4" />
                <span>Код действует {Math.floor(expiresIn / 60)} минут</span>
              </div>
            )}
            {fullUrl && (
              <Button asChild className="w-full gap-2">
                <a href={fullUrl} target="_blank" rel="noopener noreferrer">
                  <IconExternalLink className="h-4 w-4" />Открыть бота
                </a>
              </Button>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
