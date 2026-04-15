'use client';

import { useCallback, useMemo, useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import {
  Table,
  TableBody,
  TableCell,
  TableRow,
} from '@/components/ui/table';
import { AddActivityDialog } from '@/components/admin/AddActivityDialog';
import { TooltipProvider } from '@/components/ui/tooltip';
import { JournalTableHeader } from './JournalTableHeader';
import { JournalTableStudentRow } from './JournalTableStudentRow';
import type { Lesson, Student, GradeData } from '../lib/journal-constants';
import type { AttestationResult } from '@/lib/api';
import { buildMaxWorkNumberMap, sortJournalLessons } from './journalTableModel';

interface JournalTableProps {
  lessons: Lesson[];
  students: Student[];
  attendance: Record<string, Record<string, string>>;
  grades: Record<string, Record<string, GradeData>>;
  attestationScores?: Record<string, AttestationResult>;
  attestationPeriod?: 'first' | 'second';
  onAttendanceChange: (lessonId: string, studentId: string, status: string | null) => void;
  onGradeChange: (lessonId: string, studentId: string, grade: number | null, workNumber: number | null) => void;
  onLessonClick?: (lesson: Lesson) => void;
  onStudentAttestationClick?: (student: Student, attestation: AttestationResult) => void;
  onActivityAdded?: () => void;
}

export function JournalTable({
  lessons,
  students,
  attendance,
  grades,
  attestationScores,
  attestationPeriod,
  onAttendanceChange,
  onGradeChange,
  onLessonClick,
  onStudentAttestationClick,
  onActivityAdded,
}: JournalTableProps) {
  const [activityDialogOpen, setActivityDialogOpen] = useState(false);
  const [selectedStudentForActivity, setSelectedStudentForActivity] = useState<Student | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const sortedLessons = useMemo(() => sortJournalLessons(lessons), [lessons]);
  const maxWorkNumbers = useMemo(() => buildMaxWorkNumberMap(sortedLessons), [sortedLessons]);
  const columnCount = lessons.length + 2 + (attestationScores ? 1 : 0);
  const handleOpenActivityDialog = useCallback((student: Student) => {
    setSelectedStudentForActivity(student);
    setActivityDialogOpen(true);
  }, []);
  // eslint-disable-next-line react-hooks/incompatible-library
  const rowVirtualizer = useVirtualizer({
    count: students.length,
    getScrollElement: () => scrollContainerRef.current,
    estimateSize: () => 52,
    overscan: 4,
  });
  const virtualRows = rowVirtualizer.getVirtualItems();
  const paddingTop = virtualRows[0]?.start ?? 0;
  const paddingBottom = virtualRows.length > 0
    ? rowVirtualizer.getTotalSize() - (virtualRows[virtualRows.length - 1]?.end ?? 0)
    : 0;

  return (
    <TooltipProvider delayDuration={300}>
      <div ref={scrollContainerRef} className="relative overflow-auto max-h-[70vh] rounded-lg border">
        <Table>
          <JournalTableHeader
            lessons={sortedLessons}
            hasAttestationScores={Boolean(attestationScores)}
            onLessonClick={onLessonClick}
          />
          <TableBody>
            {paddingTop > 0 && (
              <TableRow aria-hidden>
                <TableCell colSpan={columnCount} className="p-0 border-0" style={{ height: `${paddingTop}px` }} />
              </TableRow>
            )}
            {virtualRows.map((virtualRow) => {
              const student = students[virtualRow.index];

              return (
                <JournalTableStudentRow
                  key={student.id}
                  index={virtualRow.index}
                  student={student}
                  lessons={sortedLessons}
                  attendance={attendance}
                  grades={grades}
                  maxWorkNumbers={maxWorkNumbers}
                  attestationScores={attestationScores}
                  attestationPeriod={attestationPeriod}
                  onAttendanceChange={onAttendanceChange}
                  onGradeChange={onGradeChange}
                  onStudentAttestationClick={onStudentAttestationClick}
                  onOpenActivityDialog={handleOpenActivityDialog}
                />
              );
            })}
            {paddingBottom > 0 && (
              <TableRow aria-hidden>
                <TableCell colSpan={columnCount} className="p-0 border-0" style={{ height: `${paddingBottom}px` }} />
              </TableRow>
            )}
          </TableBody>
        </Table>

        {selectedStudentForActivity && attestationPeriod && (
          <AddActivityDialog
            open={activityDialogOpen}
            onOpenChange={setActivityDialogOpen}
            targetId={selectedStudentForActivity.id}
            targetName={selectedStudentForActivity.full_name}
            mode="student"
            onSuccess={() => {
              setSelectedStudentForActivity(null);
              onActivityAdded?.();
            }}
          />
        )}
      </div>
    </TooltipProvider>
  );
}
