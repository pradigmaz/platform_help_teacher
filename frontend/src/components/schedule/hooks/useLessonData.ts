'use client';

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import type { Student, LessonData, LessonStatus, AttendanceStatus } from '../types';
import { ATTENDANCE_CYCLE } from '../constants';

interface UseLessonDataProps {
  lesson: LessonData | null;
  isOpen: boolean;
}

interface UseLessonDataReturn {
  students: Student[];
  attendance: Record<string, AttendanceStatus | null>;
  grades: Record<string, number | null>;
  topic: string;
  status: LessonStatus;
  isLoading: boolean;
  hasChanges: boolean;
  setTopic: (topic: string) => void;
  setStatus: (status: LessonStatus) => void;
  cycleAttendance: (studentId: string) => void;
  setGrade: (studentId: string, grade: number) => void;
  saveAll: () => Promise<void>;
  resetChanges: () => void;
}

export function useLessonData({ lesson, isOpen }: UseLessonDataProps): UseLessonDataReturn {
  const [students, setStudents] = useState<Student[]>([]);
  const [attendance, setAttendance] = useState<Record<string, AttendanceStatus | null>>({});
  const [grades, setGrades] = useState<Record<string, number | null>>({});
  const [topic, setTopicState] = useState('');
  const [status, setStatusState] = useState<LessonStatus>('normal');
  const [isLoading, setIsLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const loadData = useCallback(async () => {
    if (!lesson) return;
    setIsLoading(true);

    try {
      // Load students
      if (lesson.group_id) {
        try {
          const { data: groupData } = await api.get(`/groups/${lesson.group_id}`);
          let studentsList = groupData.students || [];
          
          if (lesson.subgroup !== null && lesson.subgroup !== undefined) {
            studentsList = studentsList.filter(
              (s: Student) => s.subgroup === lesson.subgroup
            );
          }
          setStudents(studentsList);
        } catch {
          console.warn('Could not load group');
          setStudents([]);
        }
      }

      // Load attendance
      if (lesson.group_id) {
        const { data: attData } = await api.get('/admin/journal/attendance', {
          params: { group_id: lesson.group_id, lesson_ids: [lesson.id] }
        });
        const attMap: Record<string, AttendanceStatus | null> = {};
        for (const a of attData) {
          attMap[a.student_id] = a.status as AttendanceStatus;
        }
        setAttendance(attMap);
      }

      // Load grades
      const { data: gradeData } = await api.get('/admin/journal/grades', {
        params: { lesson_ids: [lesson.id] }
      });
      const gradeMap: Record<string, number | null> = {};
      for (const g of gradeData) {
        gradeMap[g.student_id] = g.grade;
      }
      setGrades(gradeMap);

      // Set initial values
      setTopicState(lesson.topic || '');
      setStatusState(lesson.is_cancelled ? 'cancelled' : lesson.ended_early ? 'early' : 'normal');
      setHasChanges(false);
    } catch (err) {
      console.error('Ошибка загрузки данных занятия', err);
    } finally {
      setIsLoading(false);
    }
  }, [lesson]);

  useEffect(() => {
    if (lesson && isOpen) {
      loadData();
    }
  }, [lesson?.id, isOpen, loadData]);

  const setTopic = (value: string) => {
    setTopicState(value);
    setHasChanges(true);
  };

  const setStatus = (value: LessonStatus) => {
    setStatusState(value);
    setHasChanges(true);
  };

  const cycleAttendance = (studentId: string) => {
    setAttendance(prev => {
      const current = prev[studentId];
      if (!current) return { ...prev, [studentId]: 'PRESENT' };
      const idx = ATTENDANCE_CYCLE.indexOf(current);
      const next = ATTENDANCE_CYCLE[(idx + 1) % ATTENDANCE_CYCLE.length];
      return { ...prev, [studentId]: next };
    });
    setHasChanges(true);
  };

  const setGrade = (studentId: string, grade: number) => {
    setGrades(prev => ({
      ...prev,
      [studentId]: prev[studentId] === grade ? null : grade
    }));
    if (!attendance[studentId]) {
      setAttendance(prev => ({ ...prev, [studentId]: 'PRESENT' }));
    }
    setHasChanges(true);
  };

  const saveAll = async () => {
    if (!lesson) return;
    setIsLoading(true);

    try {
      // Save attendance
      const attRecords = Object.entries(attendance)
        .filter(([_, status]) => status)
        .map(([student_id, status]) => ({ student_id, status }));
      
      if (attRecords.length > 0) {
        await api.post('/admin/journal/attendance/bulk', {
          lesson_id: lesson.id,
          records: attRecords
        });
      }

      // Save grades
      for (const [student_id, grade] of Object.entries(grades)) {
        if (grade) {
          await api.post('/admin/journal/grades', {
            lesson_id: lesson.id,
            student_id,
            grade,
            work_number: lesson.work_number
          });
        }
      }

      // Save status
      if (status !== 'normal' || lesson.is_cancelled || lesson.ended_early) {
        await api.patch(`/admin/schedule/lessons/${lesson.id}`, {
          is_cancelled: status === 'cancelled',
          ended_early: status === 'early'
        });
      }

      // Save topic
      if (topic !== (lesson.topic || '')) {
        await api.patch(`/admin/schedule/lessons/${lesson.id}`, { topic });
      }

      setHasChanges(false);
    } catch (err) {
      console.error('Ошибка сохранения', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const resetChanges = () => {
    if (lesson) {
      setTopicState(lesson.topic || '');
      setStatusState(lesson.is_cancelled ? 'cancelled' : lesson.ended_early ? 'early' : 'normal');
    }
    setHasChanges(false);
  };

  return {
    students,
    attendance,
    grades,
    topic,
    status,
    isLoading,
    hasChanges,
    setTopic,
    setStatus,
    cycleAttendance,
    setGrade,
    saveAll,
    resetChanges,
  };
}
