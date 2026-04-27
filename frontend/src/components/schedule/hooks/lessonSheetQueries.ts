'use client';

import api from '@/lib/api';
import type {
  AttendanceStatus,
  Student,
  StudentGradeData,
} from '../types';
import { buildGradeMap, type LessonSnapshot } from './lessonSheetState';

interface LessonSheetResources {
  students: Student[];
  attendance: Record<string, AttendanceStatus | null>;
  grades: Record<string, StudentGradeData>;
  availableWorkNumbers: number[];
}

export async function loadLessonSheetResources(
  currentLesson: LessonSnapshot
): Promise<LessonSheetResources> {
  const students = await loadLessonStudents(currentLesson);
  const attendance = await loadLessonAttendance(currentLesson);
  const grades = await loadLessonGrades(currentLesson.id);
  const availableWorkNumbers = await loadAvailableWorkNumbers(currentLesson.subject_id);

  return {
    students,
    attendance,
    grades,
    availableWorkNumbers,
  };
}

async function loadLessonStudents(currentLesson: LessonSnapshot): Promise<Student[]> {
  if (!currentLesson.group_id) {
    return [];
  }

  try {
    const { data: students } = await api.get<Student[]>(`/admin/groups/${currentLesson.group_id}/students`);

    if (currentLesson.subgroup === null || currentLesson.subgroup === undefined) {
      return students;
    }

    return students.filter((student: Student) => student.subgroup === currentLesson.subgroup);
  } catch {
    console.warn('Could not load group');
    return [];
  }
}

async function loadLessonAttendance(
  currentLesson: LessonSnapshot
): Promise<Record<string, AttendanceStatus | null>> {
  if (!currentLesson.group_id) {
    return {};
  }

  try {
    const { data: attendanceData } = await api.get('/admin/journal/attendance', {
      params: { group_id: currentLesson.group_id, lesson_ids: [currentLesson.id] },
    });

    return Object.fromEntries(
      attendanceData.map((record: { student_id: string; status: AttendanceStatus }) => [
        record.student_id,
        record.status,
      ])
    ) as Record<string, AttendanceStatus | null>;
  } catch {
    return {};
  }
}

async function loadLessonGrades(lessonId: string): Promise<Record<string, StudentGradeData>> {
  try {
    const { data: gradeData } = await api.get('/admin/journal/grades', {
      params: { lesson_ids: [lessonId] },
    });
    return buildGradeMap(gradeData);
  } catch {
    return {};
  }
}

async function loadAvailableWorkNumbers(subjectId?: string | null): Promise<number[]> {
  if (!subjectId) {
    return [];
  }

  try {
    const { data: labs } = await api.get<Array<{ number: number }>>('/admin/labs', {
      params: {
        subject_id: subjectId,
        limit: 500,
      },
    });

    return Array.from(
      new Set(
        labs
          .map((lab) => lab.number)
          .filter((number): number is number => Number.isInteger(number) && number > 0)
      )
    ).sort((left, right) => left - right);
  } catch {
    return [];
  }
}
