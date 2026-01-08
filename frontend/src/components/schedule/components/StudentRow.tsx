'use client';

import { cn } from '@/lib/utils';
import { NoteButton } from '@/components/notes';
import type { Student, AttendanceStatus } from '../types';
import { ATTENDANCE_CONFIG } from '../constants';

interface StudentRowProps {
  student: Student;
  index: number;
  attendance: AttendanceStatus | null;
  grade: number | null;
  canHaveGrade: boolean;
  onAttendanceClick: () => void;
  onGradeClick: (grade: number) => void;
}

export function StudentRow({
  student,
  index,
  attendance,
  grade,
  canHaveGrade,
  onAttendanceClick,
  onGradeClick,
}: StudentRowProps) {
  const attConfig = attendance ? ATTENDANCE_CONFIG[attendance] : null;
  const AttIcon = attConfig?.icon;

  return (
    <div
      className={cn(
        'grid grid-cols-[32px_1fr_32px_40px_100px] gap-2 px-3 py-2 items-center text-sm group',
        index % 2 === 0 ? 'bg-background' : 'bg-muted/30'
      )}
    >
      <span className="text-muted-foreground text-xs">{index + 1}</span>
      <span className="truncate" title={student.full_name}>{student.full_name}</span>
      <NoteButton entityType="student" entityId={student.id} size="sm" />
      <button
        onClick={onAttendanceClick}
        className={cn(
          'h-7 w-7 rounded-full flex items-center justify-center transition-all hover:scale-110 mx-auto',
          attConfig ? `${attConfig.color} ${attConfig.bg}` : 'text-muted-foreground/50'
        )}
        title={attConfig?.label || 'Не отмечено'}
      >
        {AttIcon ? <AttIcon className="h-4 w-4" /> : <span>—</span>}
      </button>
      <div className="flex justify-center gap-1 opacity-50 group-hover:opacity-100 transition-opacity">
        {canHaveGrade && [2, 3, 4, 5].map((g) => (
          <button
            key={g}
            onClick={() => onGradeClick(g)}
            className={cn(
              'w-6 h-6 rounded text-xs font-bold transition-all',
              grade === g
                ? 'bg-primary text-primary-foreground scale-110'
                : 'bg-muted text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            {g}
          </button>
        ))}
      </div>
    </div>
  );
}
