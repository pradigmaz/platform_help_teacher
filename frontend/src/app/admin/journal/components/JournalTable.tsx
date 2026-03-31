'use client';

import { useState } from 'react';
import {
  Table,
  TableBody,
} from '@/components/ui/table';
import { AddActivityDialog } from '@/components/admin/AddActivityDialog';
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
  const sortedLessons = sortJournalLessons(lessons);
  const maxWorkNumbers = buildMaxWorkNumberMap(sortedLessons);

  return (
    <div className="relative overflow-auto max-h-[70vh] rounded-lg border">
      <Table>
        <JournalTableHeader
          lessons={sortedLessons}
          hasAttestationScores={Boolean(attestationScores)}
          onLessonClick={onLessonClick}
        />
        <TableBody>
          {students.map((student, index) => (
            <JournalTableStudentRow
              key={student.id}
              index={index}
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
              onOpenActivityDialog={(nextStudent) => {
                setSelectedStudentForActivity(nextStudent);
                setActivityDialogOpen(true);
              }}
            />
          ))}
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
  );
}
