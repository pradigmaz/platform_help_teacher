'use client';

import { RefreshCw, Copy, ExternalLink, Clock } from 'lucide-react';
import { IconBrandVk } from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { LinkVkResponse } from '@/lib/api';
import type { AdminProfile } from '@/lib/api/admin';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface VkCardProps {
  profile: AdminProfile | null;
  vkData: LinkVkResponse | null;
  vkDialogOpen: boolean;
  vkLoading: boolean;
  onLink: () => void;
  onDialogChange: (open: boolean) => void;
}

export function VkCard({
  profile, vkData, vkDialogOpen, vkLoading,
  onLink, onDialogChange
}: VkCardProps) {
  const copyCode = () => {
    if (vkData?.code) {
      navigator.clipboard.writeText(vkData.code);
      toast.success('Код скопирован');
    }
  };

  return (
    <>
      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-600/10">
              <IconBrandVk className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <CardTitle className="text-lg">ВКонтакте аккаунт</CardTitle>
              <CardDescription>Привязка ВК для уведомлений</CardDescription>
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
            <Button variant="outline" onClick={onLink} disabled={vkLoading} className="gap-2">
              <RefreshCw className={cn("h-4 w-4", vkLoading && "animate-spin")} />
              {profile?.vk_id ? 'Перепривязать' : 'Привязать'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={vkDialogOpen} onOpenChange={onDialogChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <IconBrandVk className="h-5 w-5 text-blue-600" />
              Привязка ВКонтакте
            </DialogTitle>
            <DialogDescription>Отправьте команду боту в ВК</DialogDescription>
          </DialogHeader>
          
          {vkData && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
                <Label className="text-xs text-muted-foreground mb-2 block">Ваш код</Label>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-2xl font-mono font-bold tracking-wider text-primary">{vkData.code}</code>
                  <Button variant="ghost" size="icon" onClick={copyCode}><Copy className="h-4 w-4" /></Button>
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
                    <ExternalLink className="h-4 w-4" />Открыть бота ВК
                  </a>
                </Button>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
