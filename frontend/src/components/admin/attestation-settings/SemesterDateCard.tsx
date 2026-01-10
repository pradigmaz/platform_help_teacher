'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Calendar, AlertCircle } from 'lucide-react';
import type { AttestationFormState } from './types';
import { formatPeriod } from './types';

interface SemesterDateCardProps {
  form: AttestationFormState;
  attestationType: 'first' | 'second';
  onUpdate: <K extends keyof AttestationFormState>(key: K, value: AttestationFormState[K]) => void;
}

export function SemesterDateCard({ form, attestationType, onUpdate }: SemesterDateCardProps) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-4 h-4 text-blue-500" />
              <Label>Дата начала семестра</Label>
            </div>
            <Input 
              type="date" 
              value={form.semester_start_date} 
              onChange={e => onUpdate('semester_start_date', e.target.value)} 
              disabled={attestationType === 'second'}
            />
          </div>
          {form.semester_start_date && (
            <div className="flex-1 text-sm space-y-1">
              <p className="text-muted-foreground">Периоды аттестаций:</p>
              <p><span className="font-medium">1-я:</span> {formatPeriod(form.semester_start_date, 1, 7)}</p>
              <p className={attestationType === 'second' ? '' : 'text-muted-foreground'}>
                <span className="font-medium">2-я:</span> {formatPeriod(form.semester_start_date, 8, 14)}
              </p>
            </div>
          )}
        </div>
        {!form.semester_start_date && (
          <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />Укажите для автовычисления периодов
          </p>
        )}
      </CardContent>
    </Card>
  );
}
