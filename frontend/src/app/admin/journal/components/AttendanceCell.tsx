'use client';

import { cn } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { STATUS_INFO } from '../lib/journal-constants';

interface AttendanceCellProps {
  status: string | undefined;
  onStatusChange: (status: string | null) => void;
}

const CYCLE_ORDER = ['PRESENT', 'LATE', 'EXCUSED', 'ABSENT'];

export function AttendanceCell({ status, onStatusChange }: AttendanceCellProps) {
  const cycleStatus = () => {
    if (!status) {
      onStatusChange('PRESENT');
      return;
    }
    const currentIndex = CYCLE_ORDER.indexOf(status);
    const nextIndex = (currentIndex + 1) % CYCLE_ORDER.length;
    onStatusChange(CYCLE_ORDER[nextIndex]);
  };

  const StatusIcon = status ? STATUS_INFO[status]?.icon : null;
  const statusColor = status ? STATUS_INFO[status]?.color : 'text-muted-foreground/50';
  const statusBg = status ? STATUS_INFO[status]?.color.replace('text-', 'bg-').replace('-600', '-500/15') : '';

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button 
          onClick={(e) => {
            // Left click = cycle, right click = menu (handled by dropdown)
            if (e.detail === 1 && e.button === 0) {
              e.preventDefault();
              cycleStatus();
            }
          }}
          className={cn(
            'h-6 w-6 p-0 rounded-full transition-all hover:scale-110 flex items-center justify-center',
            statusColor,
            statusBg,
            'hover:bg-accent'
          )}
          title={status ? STATUS_INFO[status]?.label : 'Не отмечено (клик = перебор, ПКМ = меню)'}
        >
          {StatusIcon ? <StatusIcon className="w-3.5 h-3.5" /> : <span className="text-xs">—</span>}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="center" className="min-w-[140px]">
        {Object.entries(STATUS_INFO).map(([key, info]) => (
          <DropdownMenuItem 
            key={key}
            onClick={() => onStatusChange(key)}
            className="cursor-pointer"
          >
            <info.icon className={`w-4 h-4 mr-2 ${info.color}`} />
            {info.label}
          </DropdownMenuItem>
        ))}
        {status && (
          <DropdownMenuItem 
            onClick={() => onStatusChange(null)}
            className="cursor-pointer text-destructive"
          >
            <span className="w-4 h-4 mr-2 flex items-center justify-center">×</span>
            Сбросить
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
