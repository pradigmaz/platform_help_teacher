'use client';

import { Eye, EyeOff, Users, FileText } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

export function VisibilityInfoCard() {
  return (
    <Card className="border-dashed bg-muted/30">
      <CardContent className="pt-6">
        <div className="flex gap-4">
          <div className="p-2 rounded-lg bg-amber-500/10 h-fit">
            <Eye className="h-5 w-5 text-amber-500" />
          </div>
          <div className="space-y-2">
            <h3 className="font-medium">Как работает видимость?</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <Users className="h-3.5 w-3.5" />
                <span><strong>Студентам</strong> — контакт виден в личном кабинете студента</span>
              </li>
              <li className="flex items-center gap-2">
                <FileText className="h-3.5 w-3.5" />
                <span><strong>В отчёте</strong> — контакт виден в публичном отчёте для родителей</span>
              </li>
              <li className="flex items-center gap-2">
                <Eye className="h-3.5 w-3.5" />
                <span><strong>Везде</strong> — контакт виден и студентам, и в отчёте</span>
              </li>
              <li className="flex items-center gap-2">
                <EyeOff className="h-3.5 w-3.5" />
                <span><strong>Скрыто</strong> — контакт нигде не отображается</span>
              </li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
