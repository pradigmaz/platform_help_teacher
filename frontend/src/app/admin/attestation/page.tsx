'use client';

import Link from 'next/link';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AttestationSettingsForm } from '@/components/admin/AttestationSettingsForm';

export default function AttestationPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-800 dark:text-amber-300 md:flex-row md:items-center md:justify-between">
        <div className="flex gap-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            <div className="font-medium">Числовые пороги аттестации больше не редактируются глобально</div>
            <div className="text-xs opacity-90">
              На этой странице остаются общие веса и коэффициенты. Пороги лабораторных, допуск и автомат задаются по связке.
            </div>
          </div>
        </div>
        <Button variant="outline" asChild className="bg-background/80">
          <Link href="/admin/labs">Открыть раздел лабораторных</Link>
        </Button>
      </div>
      <AttestationSettingsForm />
    </div>
  );
}
