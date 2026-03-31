'use client';

import { Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TableCell, TableRow } from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { NoteButton } from '@/components/notes';
import { AttendanceCell } from './AttendanceCell';
import { GradeCell } from './GradeCell';
import { canHaveGrade } from '../lib/journal-constants';
import type { GradeData, Lesson, Student } from '../lib/journal-constants';
import type { AttestationResult } from '@/lib/api';
import {
  buildJournalStudentRowModel,
  getAttestationGradeColor,
  isLessonDisabledForStudent,
} from './journalTableModel';

interface JournalTableStudentRowProps {
  index: number;
  student: Student;
  lessons: Lesson[];
  attendance: Record<string, Record<string, string>>;
  grades: Record<string, Record<string, GradeData>>;
  maxWorkNumbers: Record<string, number>;
  attestationScores?: Record<string, AttestationResult>;
  attestationPeriod?: 'first' | 'second';
  onAttendanceChange: (lessonId: string, studentId: string, status: string | null) => void;
  onGradeChange: (lessonId: string, studentId: string, grade: number | null, workNumber: number | null) => void;
  onStudentAttestationClick?: (student: Student, attestation: AttestationResult) => void;
  onOpenActivityDialog: (student: Student) => void;
}

export function JournalTableStudentRow({
  index,
  student,
  lessons,
  attendance,
  grades,
  maxWorkNumbers,
  attestationScores,
  attestationPeriod,
  onAttendanceChange,
  onGradeChange,
  onStudentAttestationClick,
  onOpenActivityDialog,
}: JournalTableStudentRowProps) {
  const isEven = index % 2 === 0;
  const rowModel = buildJournalStudentRowModel(lessons, attendance, grades, attestationScores, student.id);

  return (
    <TableRow className={`${isEven ? 'bg-background' : 'bg-muted/30'} hover:bg-accent/50 transition-colors`}>
      <TableCell className={`sticky left-0 z-10 font-medium border-r ${isEven ? 'bg-background' : 'bg-muted/30'} hover:bg-accent/50`}>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground text-xs w-5">{index + 1}.</span>
          <span title={student.full_name}>{student.full_name}</span>
          {student.subgroup && (
            <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 shrink-0">
              {student.subgroup}п.г.
            </Badge>
          )}
          <div className="flex items-center gap-0.5 ml-auto shrink-0">
            <NoteButton entityType="student" entityId={student.id} size="sm" />
            {attestationPeriod && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 text-muted-foreground hover:text-primary"
                      onClick={(event) => {
                        event.stopPropagation();
                        onOpenActivityDialog(student);
                      }}
                    >
                      <Sparkles className="h-3.5 w-3.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>Добавить активность</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
        </div>
      </TableCell>

      {lessons.map((lesson) => {
        const status = rowModel.attendanceByLesson[lesson.id];
        const gradeData = rowModel.gradesByLesson[lesson.id];
        const showGrade = canHaveGrade(lesson);
        const isDisabled = isLessonDisabledForStudent(lesson, student);

        return (
          <TableCell
            key={lesson.id}
            className={`text-center p-1 ${
              isDisabled ? 'bg-muted/70 opacity-40' : 'hover:bg-accent/30 cursor-pointer border border-border/50'
            }`}
          >
            {isDisabled ? (
              <div className="h-8 flex items-center justify-center">
                <span className="text-muted-foreground/50 text-xs">—</span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-0.5">
                <AttendanceCell
                  status={status}
                  onStatusChange={(nextStatus) => onAttendanceChange(lesson.id, student.id, nextStatus)}
                />
                {showGrade && (
                  <GradeCell
                    gradeData={gradeData}
                    lesson={lesson}
                    maxWorkNum={maxWorkNumbers[lesson.lesson_type.toLowerCase()] ?? 0}
                    onGradeChange={(grade, workNumber) => onGradeChange(lesson.id, student.id, grade, workNumber)}
                  />
                )}
              </div>
            )}
          </TableCell>
        );
      })}

      {attestationScores && (
        <TableCell className={`text-center border-l ${isEven ? 'bg-background' : 'bg-muted/30'}`}>
          {rowModel.attestation ? (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    className={`px-2 py-1 rounded-md text-sm font-semibold cursor-pointer transition-colors hover:opacity-80 ${getAttestationGradeColor(rowModel.attestation.grade)}`}
                    onClick={() => onStudentAttestationClick?.(student, rowModel.attestation!)}
                  >
                    {rowModel.attestation.total_score.toFixed(1)}
                  </button>
                </TooltipTrigger>
                <TooltipContent side="left" className="p-3 max-w-[200px]">
                  <div className="space-y-1.5 text-xs">
                    <div className="font-semibold border-b pb-1 mb-1">
                      {rowModel.attestation.grade.toUpperCase()} ({rowModel.attestation.total_score.toFixed(1)}/{rowModel.attestation.max_points})
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Лабы:</span>
                      <span>{rowModel.attestation.breakdown.labs_score.toFixed(1)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Посещ.:</span>
                      <span>{rowModel.attestation.breakdown.attendance_score.toFixed(1)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Актив.:</span>
                      <span>{rowModel.attestation.breakdown.activity_score.toFixed(1)}</span>
                    </div>
                    {!rowModel.attestation.is_passing && (
                      <div className="text-red-500 text-[10px] pt-1 border-t mt-1">
                        Не хватает {(rowModel.attestation.min_passing_points - rowModel.attestation.total_score).toFixed(1)} б.
                      </div>
                    )}
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <span className="text-sm text-muted-foreground">—</span>
          )}
        </TableCell>
      )}

      <TableCell className={`sticky right-0 z-10 text-center font-semibold border-l ${isEven ? 'bg-background' : 'bg-muted/30'}`}>
        {rowModel.percentage !== null ? (
          <span
            className={`text-sm ${
              rowModel.percentage < 60 ? 'text-red-600' : rowModel.percentage < 80 ? 'text-yellow-600' : 'text-green-600'
            }`}
          >
            {rowModel.percentage}%
          </span>
        ) : (
          <span className="text-sm text-muted-foreground">—</span>
        )}
      </TableCell>
    </TableRow>
  );
}
