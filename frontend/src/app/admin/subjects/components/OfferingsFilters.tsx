'use client';

import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { FinalControlType } from '@/lib/api';

export type OfferingControlFilter = 'all' | 'unset' | FinalControlType;

interface OfferingsFiltersProps {
  search: string;
  controlFilter: OfferingControlFilter;
  subjectOptions: string[];
  selectedSubject: string;
  onSearchChange: (value: string) => void;
  onControlFilterChange: (value: OfferingControlFilter) => void;
  onSubjectChange: (value: string) => void;
}

export function OfferingsFilters({
  search,
  controlFilter,
  subjectOptions,
  selectedSubject,
  onSearchChange,
  onControlFilterChange,
  onSubjectChange,
}: OfferingsFiltersProps) {
  return (
    <div className="grid grid-cols-1 gap-3 rounded-xl border border-border/60 bg-background/80 p-4 lg:grid-cols-[1.4fr_220px_240px]">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Найти группу или предмет"
          className="pl-9"
        />
      </div>
      <Select value={selectedSubject} onValueChange={onSubjectChange}>
        <SelectTrigger>
          <SelectValue placeholder="Все предметы" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все предметы</SelectItem>
          {subjectOptions.map((subject) => (
            <SelectItem key={subject} value={subject}>
              {subject}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={controlFilter} onValueChange={(value) => onControlFilterChange(value as OfferingControlFilter)}>
        <SelectTrigger>
          <SelectValue placeholder="Все формы контроля" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все формы контроля</SelectItem>
          <SelectItem value="unset">Не задано</SelectItem>
          <SelectItem value="exam">Экзамен</SelectItem>
          <SelectItem value="credit">Зачёт</SelectItem>
          <SelectItem value="differentiated_credit">Диф. зачёт</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
