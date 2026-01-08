'use client';

import { Users } from 'lucide-react';
import { Label } from '@/components/ui/label';
import type { Student, AttendanceStatus } from '../types';
import { StudentRow } from './StudentRow';

interface StudentsTableProps {
  students: Student[];
  attendance: Record<string, AttendanceStatus | null>;
  grades: Record<string, number | null>;
  canHaveGrade: boolean;
  isLoading: boolean;
  onAttendanceClick: (studentId: string) => void;
  onGradeClick: (studentId: string, grade: number) => void;
}

export function StudentsTable({
  students,
  attendance,
  grades,
  canHaveGrade,
  isLoading,
  onAttendanceClick,
  onGradeClick,
}: StudentsTableProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
          <Users className="h-3 w-3" />
          Студенты ({students.length})
        </Label>
        <div className="flex gap-2 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> Присут.
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-rose-500" /> Н/Б
          </span>
        </div>
      </div>

      <div className="border rounded-lg overflow-hidden">
        {/* Table header */}
        <div className="grid grid-cols-[32px_1fr_32px_40px_100px] gap-2 px-3 py-2 bg-muted text-[10px] font-medium text-muted-foreground uppercase">
          <span>#</span>
          <span>ФИО</span>
          <span></span>
          <span className="text-center">Посещ.</span>
          <span className="text-center">Оценка</span>
        </div>

        {/* Rows */}
        <div className="divide-y max-h-[340px] overflow-y-auto">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground text-sm">Загрузка...</div>
          ) : (
            students.map((student, idx) => (
              <StudentRow
                key={student.id}
                student={student}
                index={idx}
                attendance={attendance[student.id] || null}
                grade={grades[student.id] || null}
                canHaveGrade={canHaveGrade}
                onAttendanceClick={() => onAttendanceClick(student.id)}
                onGradeClick={(grade) => onGradeClick(student.id, grade)}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
