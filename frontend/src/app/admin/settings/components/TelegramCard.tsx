'use client';

import { RefreshCw, Copy, ExternalLink, Clock } from 'lucide-react';
import { IconBrandTelegram } from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { RelinkTelegramResponse } from '@/lib/api';
import type { AdminProfile } from '@/lib/api/admin';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface TelegramCardProps {
  profile: AdminProfile | null;
  relinkData: RelinkTelegramResponse | null;
  relinkDialogOpen: boolean;
  relinkLoading: boolean;
  onRelink: () => void;
  onDialogChange: (open: boolean) => void;
}

export function TelegramCard({
  profile, relinkData, relinkDialogOpen, relinkLoading,
  onRelink, onDialogChange
}: TelegramCardProps) {
  const copyCode = () => {
    if (relinkData?.code) {
      navigator.clipboard.writeText(relinkData.code);
      toast.success('Код скопирован');
    }
  };

  return (
    <>
      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <IconBrandTelegram className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <CardTitle className="text-lg">Telegram аккаунт</CardTitle>
              <CardDescription>Управление привязкой Telegram для авторизации</CardDescription>
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
            <Button variant="outline" onClick={onRelink} disabled={relinkLoading} className="gap-2">
              <RefreshCw className={cn("h-4 w-4", relinkLoading && "animate-spin")} />
              Перепривязать
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={relinkDialogOpen} onOpenChange={onDialogChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <IconBrandTelegram className="h-5 w-5 text-blue-400" />
              Перепривязка Telegram
            </DialogTitle>
            <DialogDescription>Отправьте команду боту с нового Telegram аккаунта</DialogDescription>
          </DialogHeader>
          
          {relinkData && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-neutral-100 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
                <Label className="text-xs text-muted-foreground mb-2 block">Ваш код</Label>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-2xl font-mono font-bold tracking-wider text-primary">{relinkData.code}</code>
                  <Button variant="ghost" size="icon" onClick={copyCode}><Copy className="h-4 w-4" /></Button>
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
                    <ExternalLink className="h-4 w-4" />Открыть бота
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
