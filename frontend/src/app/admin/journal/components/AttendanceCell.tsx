'use client';

import { cn } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { STATUS_INFO } from '../lib/journal-constants';

interface AttendanceCellProps {
  status: string | undefined;
  onStatusChange: (status: string | null) => void;
}

const CYCLE_ORDER = ['PRESENT', 'LATE', 'EXCUSED', 'ABSENT'];

// Get next status in cycle
function getNextStatus(current: string | undefined): string {
  if (!current) return 'PRESENT';
  const currentIndex = CYCLE_ORDER.indexOf(current);
  const nextIndex = (currentIndex + 1) % CYCLE_ORDER.length;
  return CYCLE_ORDER[nextIndex];
}

export function AttendanceCell({ status, onStatusChange }: AttendanceCellProps) {
  const cycleStatus = () => {
    onStatusChange(getNextStatus(status));
  };

  const StatusIcon = status ? STATUS_INFO[status]?.icon : null;
  const statusColor = status ? STATUS_INFO[status]?.color : 'text-muted-foreground/50';
  const statusBg = status ? STATUS_INFO[status]?.color.replace('text-', 'bg-').replace('-600', '-500/15') : '';
  
  const nextStatus = getNextStatus(status);
  const nextStatusLabel = STATUS_INFO[nextStatus]?.label || 'Присутствует';

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <DropdownMenu>
          <TooltipTrigger asChild>
            <DropdownMenuTrigger asChild>
              <button 
                onClick={(e) => {
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
              >
                {StatusIcon ? <StatusIcon className="w-3.5 h-3.5" /> : <span className="text-xs">—</span>}
              </button>
            </DropdownMenuTrigger>
          </TooltipTrigger>
          <TooltipContent side="top" className="text-xs">
            <p>{status ? STATUS_INFO[status]?.label : 'Не отмечено'}</p>
            <p className="text-muted-foreground">Клик → {nextStatusLabel}</p>
            <p className="text-muted-foreground">ПКМ → меню</p>
          </TooltipContent>
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
      </Tooltip>
    </TooltipProvider>
  );
}
