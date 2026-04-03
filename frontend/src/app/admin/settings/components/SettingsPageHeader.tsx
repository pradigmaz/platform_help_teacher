'use client';

import { Settings2 } from 'lucide-react';

export function SettingsPageHeader() {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-primary/10">
          <Settings2 className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Настройки</h1>
          <p className="text-muted-foreground">Управление профилем и системой</p>
        </div>
      </div>
    </div>
  );
}
