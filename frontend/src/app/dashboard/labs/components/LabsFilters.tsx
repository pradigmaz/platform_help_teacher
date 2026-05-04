'use client';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { FilterStatus } from '../types';

interface LabsFiltersProps {
  counts: Record<FilterStatus, number>;
  filter: FilterStatus;
  onFilterChange: (filter: FilterStatus) => void;
}

const FILTERS: { value: FilterStatus; label: string }[] = [
  { value: 'all', label: 'Все' },
  { value: 'not_submitted', label: 'Не сдано' },
  { value: 'in_queue', label: 'В очереди' },
  { value: 'accepted', label: 'Принято' },
  { value: 'rejected', label: 'Отклонено' },
];

export function LabsFilters({ counts, filter, onFilterChange }: LabsFiltersProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {FILTERS.map((item) => (
        <Button
          key={item.value}
          variant={filter === item.value ? 'default' : 'secondary'}
          size="sm"
          onClick={() => onFilterChange(item.value)}
          className={cn('gap-2', filter !== item.value && 'bg-card hover:bg-card/80')}
        >
          {item.label}
          <span className={cn('rounded-full px-1.5 py-0.5 text-xs', filter === item.value ? 'bg-background/20' : 'bg-muted')}>
            {counts[item.value]}
          </span>
        </Button>
      ))}
    </div>
  );
}

