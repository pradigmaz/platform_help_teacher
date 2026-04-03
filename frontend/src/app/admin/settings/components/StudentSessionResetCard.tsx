'use client';

import { Loader2, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface StudentSessionResetCardProps {
  revokeLoading: boolean;
  onRevoke: () => void;
}

export function StudentSessionResetCard({ revokeLoading, onRevoke }: StudentSessionResetCardProps) {
  return (
    <Card className="mt-6 border-destructive/50">
      <CardHeader>
        <CardTitle className="text-destructive flex items-center gap-2">
          <LogOut className="h-5 w-5" />
          Сброс сессий студентов
        </CardTitle>
        <CardDescription>
          Выкинуть всех студентов из всех сессий. Используйте для очистки сессий на общих компьютерах.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant="destructive" onClick={onRevoke} disabled={revokeLoading}>
          {revokeLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Выкидываем...
            </>
          ) : (
            <>
              <LogOut className="mr-2 h-4 w-4" />
              Выкинуть всех студентов
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
