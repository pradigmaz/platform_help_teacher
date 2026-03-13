'use client';

import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { NoteButton } from '@/components/notes';
import type { Student, AttendanceStatus, StudentGradeData } from '../types';
import { ATTENDANCE_CONFIG } from '../constants';

interface StudentRowProps {
  student: Student;
  index: number;
  attendance: AttendanceStatus | null;
  gradeData?: StudentGradeData;
  canHaveGrade: boolean;
  lessonWorkNumber: number | null;
  onAttendanceClick: () => void;
  onGradeClick: (grade: number) => void;
  onWorkNumberChange: (workNumber: number) => void;
}

export function StudentRow({
  student,
  index,
  attendance,
  gradeData,
  canHaveGrade,
  lessonWorkNumber,
  onAttendanceClick,
  onGradeClick,
  onWorkNumberChange,
}: StudentRowProps) {
  const attConfig = attendance ? ATTENDANCE_CONFIG[attendance] : null;
  const AttIcon = attConfig?.icon;
  const grade = gradeData?.grade ?? null;
  const gradeConflictCount = gradeData?.conflict_count;
  const gradeWorkNumber = grade !== null ? gradeData?.work_number ?? null : null;
  const hasMissingWorkNumber = grade !== null && gradeWorkNumber == null;
  const workNumberOptions = Array.from({ length: Math.max(lessonWorkNumber ?? 0, gradeWorkNumber ?? 0, 20) }, (_, optionIndex) => optionIndex + 1);

  return (
    <div
      className={cn(
        'grid grid-cols-[32px_1fr_32px_40px_148px] gap-2 px-3 py-2 items-center text-sm group',
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
        {gradeConflictCount ? (
          <div
            title={`У студента ${gradeConflictCount} оценки на этой паре. Разберите конфликт в журнале.`}
            className="h-6 px-2 rounded bg-destructive/15 text-destructive text-[10px] font-semibold flex items-center"
          >
            Конфликт
          </div>
        ) : null}
        {canHaveGrade && !gradeConflictCount && grade !== null ? (
          <Popover>
            <PopoverTrigger asChild>
              <button
                type="button"
                title={
                  hasMissingWorkNumber
                    ? 'Номер работы не указан'
                    : `Работа №${gradeWorkNumber}`
                }
                className={cn(
                  'h-6 px-1.5 rounded text-[10px] font-semibold flex items-center',
                  hasMissingWorkNumber
                    ? 'bg-amber-500/15 text-amber-600'
                    : 'bg-muted text-muted-foreground'
                )}
              >
                {hasMissingWorkNumber ? '№?' : `№${gradeWorkNumber}`}
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-2" align="center">
              <div className="text-xs text-muted-foreground mb-1">№ работы:</div>
              <div className="flex gap-1 flex-wrap max-w-[160px]">
                {workNumberOptions.map((workNumber) => (
                  <Button
                    key={workNumber}
                    type="button"
                    variant={gradeWorkNumber === workNumber ? 'default' : 'outline'}
                    size="sm"
                    className="h-5 w-5 p-0 text-[10px]"
                    onClick={() => onWorkNumberChange(workNumber)}
                  >
                    {workNumber}
                  </Button>
                ))}
              </div>
            </PopoverContent>
          </Popover>
        ) : null}
        {canHaveGrade && !gradeConflictCount && [2, 3, 4, 5].map((g) => (
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
