'use client';

import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { StudentDetailData } from '@/lib/api';
import type { ReportAttestation } from '../../../reportNavigation';
import { formatGroupCode } from '@/lib/utils';
import { getAttestationLabel } from './attestationSummary';

interface StudentReportHeaderProps {
  data: StudentDetailData;
  attestationType: ReportAttestation;
  onBack: () => void;
}

export function StudentReportHeader({
  data,
  attestationType,
  onBack,
}: StudentReportHeaderProps) {
  return (
    <div className="flex items-start gap-4">
      <Button variant="ghost" size="icon" onClick={onBack} className="mt-0.5 shrink-0 rounded-full">
        <ArrowLeft className="h-5 w-5" />
      </Button>
      <div className="min-w-0 space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {data.name || 'Карточка студента'}
        </h1>
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <span>Группа {formatGroupCode(data.group_code)}</span>
          <span className="hidden sm:inline">•</span>
          <span>{getAttestationLabel(attestationType)}</span>
          {data.rank_in_group && data.total_in_group && (
            <>
              <span className="hidden sm:inline">•</span>
              <span>#{data.rank_in_group} из {data.total_in_group}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
