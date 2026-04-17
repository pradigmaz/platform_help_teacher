'use client';

import { ChevronDown } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { ATTENDANCE_CONFIG } from '../constants';
import type { AttendanceStatus } from '../types';

interface AttendanceControlProps {
  status: AttendanceStatus | null;
  onStatusChange: (status: AttendanceStatus | null) => void;
  className?: string;
  disabled?: boolean;
  disabledReason?: string;
}

export function AttendanceControl({
  status,
  onStatusChange,
  className,
  disabled = false,
  disabledReason = 'Недоступно',
}: AttendanceControlProps) {
  const attConfig = status ? ATTENDANCE_CONFIG[status] : null;
  const AttIcon = attConfig?.icon;
  const label = attConfig?.label || 'Не отмечено';

  if (disabled) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            disabled
            className={cn(
              'mx-auto flex h-7 min-w-9 cursor-not-allowed items-center justify-center gap-0.5 rounded-full px-1 opacity-55',
              attConfig ? `${attConfig.color} ${attConfig.bg}` : 'text-muted-foreground/50 bg-muted/40',
              className
            )}
            aria-label="Посещаемость недоступна"
            title={disabledReason}
          >
            {AttIcon ? <AttIcon className="h-4 w-4" /> : <span>—</span>}
          </button>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs">
          <p>{label}</p>
          <p className="text-muted-foreground">{disabledReason}</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  return (
    <DropdownMenu modal={false}>
      <Tooltip>
        <TooltipTrigger asChild>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className={cn(
                'mx-auto flex h-7 min-w-9 items-center justify-center gap-0.5 rounded-full px-1 transition-all hover:scale-110',
                attConfig ? `${attConfig.color} ${attConfig.bg}` : 'text-muted-foreground/50 hover:bg-muted',
                className
              )}
              aria-label="Выбрать статус посещаемости"
              title={label}
            >
              {AttIcon ? <AttIcon className="h-4 w-4" /> : <span>—</span>}
              <ChevronDown className="h-3 w-3 opacity-75" />
            </button>
          </DropdownMenuTrigger>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs">
          <p>{label}</p>
          <p className="text-muted-foreground">Выбрать статус</p>
        </TooltipContent>
        <DropdownMenuContent align="center" className="min-w-[170px] z-[10000]">
          {Object.entries(ATTENDANCE_CONFIG).map(([key, info]) => (
            <DropdownMenuItem
              key={key}
              onClick={() => onStatusChange(key as AttendanceStatus)}
              className="cursor-pointer"
            >
              <info.icon className={cn('mr-2 h-4 w-4', info.color)} />
              {info.label}
            </DropdownMenuItem>
          ))}
          {status ? (
            <DropdownMenuItem
              onClick={() => onStatusChange(null)}
              className="cursor-pointer text-destructive focus:text-destructive"
            >
              <span className="mr-2 flex h-4 w-4 items-center justify-center">×</span>
              Сбросить
            </DropdownMenuItem>
          ) : null}
        </DropdownMenuContent>
      </Tooltip>
    </DropdownMenu>
  );
}
