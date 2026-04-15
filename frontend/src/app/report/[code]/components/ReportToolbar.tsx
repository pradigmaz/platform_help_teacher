'use client';

import { RefreshCcw, Users } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { ReportSubgroupFilter } from './reportFilters';

interface ReportToolbarProps {
  attestationType: 'first' | 'second';
  onAttestationChange: (value: string) => void;
  isSecondAvailable: boolean;
  selectedSubgroup: ReportSubgroupFilter;
  onSubgroupChange: (value: ReportSubgroupFilter) => void;
  subgroupOptions: ReportSubgroupFilter[];
  isReloading: boolean;
}

const subgroupLabels: Record<ReportSubgroupFilter, string> = {
  all: 'Все студенты',
  '1': '1 подгруппа',
  '2': '2 подгруппа',
};

export function ReportToolbar({
  attestationType,
  onAttestationChange,
  isSecondAvailable,
  selectedSubgroup,
  onSubgroupChange,
  subgroupOptions,
  isReloading,
}: ReportToolbarProps) {
  return (
    <Card className="border-border/60 shadow-sm">
      <CardContent className="flex flex-col gap-4 p-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">Период отчёта</p>
          <Tabs value={attestationType} onValueChange={onAttestationChange}>
            <TabsList className="grid w-full grid-cols-2 md:w-auto">
              <TabsTrigger value="first">1 аттестация</TabsTrigger>
              <TabsTrigger value="second" disabled={!isSecondAvailable}>
                2 аттестация
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="flex flex-col gap-2 md:min-w-[220px]">
          <p className="text-sm font-medium text-foreground">Срез по группе</p>
          <Select value={selectedSubgroup} onValueChange={(value) => onSubgroupChange(value as ReportSubgroupFilter)}>
            <SelectTrigger>
              <SelectValue placeholder="Выберите подгруппу" />
            </SelectTrigger>
            <SelectContent>
              {subgroupOptions.map((option) => (
                <SelectItem key={option} value={option}>
                  {subgroupLabels[option]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>

      <CardContent className="flex flex-col gap-2 border-t border-border/60 pt-3 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-2">
          <Users className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            Подгруппа влияет на сводку, графики и список студентов. История занятий ниже остаётся общей для всей группы.
          </p>
        </div>
        {isReloading && (
          <div className="flex items-center gap-2 text-foreground">
            <RefreshCcw className="h-4 w-4 animate-spin" />
            <span>Обновляем данные…</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
