'use client';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { NoteButton } from '@/components/notes';
import type { Student, AttendanceStatus, StudentGradeData } from '../types';
import { AttendanceControl } from './AttendanceControl';

interface StudentRowProps {
  student: Student;
  index: number;
  attendance: AttendanceStatus | null;
  gradeData?: StudentGradeData;
  canHaveGrade: boolean;
  attendanceDisabled?: boolean;
  attendanceDisabledReason?: string;
  lessonWorkNumber: number | null;
  availableWorkNumbers: number[];
  onAttendanceChange: (status: AttendanceStatus | null) => void;
  onGradeClick: (grade: number, workNumber: number | null) => void;
  onWorkNumberChange: (workNumber: number) => void;
}

export function StudentRow({
  student,
  index,
  attendance,
  gradeData,
  canHaveGrade,
  attendanceDisabled = false,
  attendanceDisabledReason,
  lessonWorkNumber,
  availableWorkNumbers,
  onAttendanceChange,
  onGradeClick,
  onWorkNumberChange,
}: StudentRowProps) {
  const grade = gradeData?.grade ?? null;
  const hasGradeConflict = gradeData?.has_conflict === true;
  const gradeConflictCount = hasGradeConflict ? gradeData?.conflict_count ?? 2 : 0;
  const gradeItems = gradeData?.grade_items ?? [];
  const hasMultiGrade = !hasGradeConflict && gradeItems.length > 1;
  const selectedWorkNumber = gradeData?.work_number ?? lessonWorkNumber ?? null;
  const selectedWorkNumberValue = availableWorkNumbers.includes(selectedWorkNumber ?? -1)
    ? selectedWorkNumber?.toString()
    : '';
  const hasMissingWorkNumber = grade !== null && !selectedWorkNumberValue;

  return (
    <div
      className={cn(
        'grid grid-cols-[32px_1fr_32px_40px_208px] gap-2 px-2 py-2 items-center text-sm group',
        index % 2 === 0 ? 'bg-background' : 'bg-muted/30'
      )}
    >
      <span className="text-muted-foreground text-xs">{index + 1}</span>
      <span className="truncate" title={student.full_name}>{student.full_name}</span>
      <NoteButton entityType="student" entityId={student.id} size="sm" />
      <AttendanceControl
        status={attendance}
        onStatusChange={onAttendanceChange}
        disabled={attendanceDisabled}
        disabledReason={attendanceDisabledReason}
      />
      <div className="flex justify-center gap-1 opacity-50 group-hover:opacity-100 transition-opacity">
        {hasGradeConflict ? (
          <div
            title={`У студента ${gradeConflictCount} оценки на этой паре. Разберите конфликт в журнале.`}
            className="h-6 px-2 rounded bg-destructive/15 text-destructive text-[10px] font-semibold flex items-center"
          >
            Конфликт
          </div>
        ) : null}
        {hasMultiGrade ? (
          <div
            title={gradeItems.map((item) => `${item.grade}(${item.work_number ?? '?'})`).join(', ')}
            className="h-6 px-2 rounded bg-primary/10 text-primary text-[10px] font-semibold flex items-center"
          >
            {gradeItems.map((item) => `${item.grade}(${item.work_number ?? '?'})`).join(', ')}
          </div>
        ) : null}
        {canHaveGrade && !hasGradeConflict && !hasMultiGrade ? (
          <Select
            value={selectedWorkNumberValue}
            onValueChange={(value) => onWorkNumberChange(parseInt(value, 10))}
          >
            <SelectTrigger
              className={cn(
                'h-6 w-[78px] px-2 text-[10px]',
                hasMissingWorkNumber && 'border-amber-500 text-amber-600'
              )}
              aria-label="Номер лабораторной"
            >
              <SelectValue placeholder="ЛР ?" />
            </SelectTrigger>
            <SelectContent className="z-[10000]">
              {availableWorkNumbers.map((workNumber) => (
                <SelectItem key={workNumber} value={workNumber.toString()}>
                  ЛР №{workNumber}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : null}
        {canHaveGrade && !hasGradeConflict && !hasMultiGrade && [2, 3, 4, 5].map((g) => (
          <button
            key={g}
            onClick={() =>
              onGradeClick(g, selectedWorkNumberValue ? parseInt(selectedWorkNumberValue, 10) : null)
            }
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
