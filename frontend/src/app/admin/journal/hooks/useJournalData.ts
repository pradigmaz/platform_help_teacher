'use client';

import { useState, useEffect, useCallback } from 'react';
import { format, startOfWeek, endOfWeek, parseISO, addWeeks, startOfYear } from 'date-fns';
import api, { AttestationAPI, AttestationType, AttestationResult } from '@/lib/api';
import type { Group, Subject, Lesson, Student, GradeData, JournalStats } from '../lib/journal-constants';

// Attestation period type
export type AttestationPeriod = 'all' | 'first' | 'second';

interface UseJournalDataProps {
  lessonIdParam: string | null;
}

interface UseJournalDataReturn {
  groups: Group[];
  subjects: Subject[];
  selectedGroupId: string;
  setSelectedGroupId: (id: string) => void;
  selectedSubjectId: string;
  setSelectedSubjectId: (id: string) => void;
  selectedLessonType: string;
  setSelectedLessonType: (type: string) => void;
  currentWeek: Date;
  setCurrentWeek: (date: Date) => void;
  attestationPeriod: AttestationPeriod;
  setAttestationPeriod: (period: AttestationPeriod) => void;
  lessons: Lesson[];
  students: Student[];
  attendance: Record<string, Record<string, string>>;
  grades: Record<string, Record<string, GradeData>>;
  attestationScores: Record<string, AttestationResult>;
  stats: JournalStats | null;
  isLoading: boolean;
  updateAttendance: (lessonId: string, studentId: string, status: string) => Promise<void>;
  updateGrade: (lessonId: string, studentId: string, grade: number, workNumber?: number | null) => Promise<void>;
}

// Helper to get attestation period date range
function getAttestationPeriodDates(period: AttestationPeriod, semesterStart: Date): { start: Date; end: Date } | null {
  if (period === 'all') return null;
  
  if (period === 'first') {
    // Weeks 1-7 (days 0-48)
    return {
      start: semesterStart,
      end: addWeeks(semesterStart, 7),
    };
  } else {
    // Weeks 8-13 (days 49-90)
    return {
      start: addWeeks(semesterStart, 7),
      end: addWeeks(semesterStart, 13),
    };
  }
}

export function useJournalData({ lessonIdParam }: UseJournalDataProps): UseJournalDataReturn {
  const [groups, setGroups] = useState<Group[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<string>('');
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('all');
  const [selectedLessonType, setSelectedLessonType] = useState<string>('all');
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [attendance, setAttendance] = useState<Record<string, Record<string, string>>>({});
  const [grades, setGrades] = useState<Record<string, Record<string, GradeData>>>({});
  const [attestationScores, setAttestationScores] = useState<Record<string, AttestationResult>>({});
  const [stats, setStats] = useState<JournalStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const [attestationPeriod, setAttestationPeriod] = useState<AttestationPeriod>('all');
  const [initialLoadDone, setInitialLoadDone] = useState(false);

  // Semester start - September 1st of current academic year
  const getSemesterStart = () => {
    const now = new Date();
    const year = now.getMonth() >= 8 ? now.getFullYear() : now.getFullYear() - 1;
    return new Date(year, 8, 1); // September 1st
  };

  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(currentWeek, { weekStartsOn: 1 });

  // Load lesson by ID from URL
  useEffect(() => {
    if (lessonIdParam && !initialLoadDone) {
      loadLessonById(lessonIdParam);
    }
  }, [lessonIdParam, initialLoadDone]);

  const loadLessonById = async (lessonId: string) => {
    try {
      const { data: lesson } = await api.get(`/admin/lessons/${lessonId}`);
      if (lesson) {
        setSelectedGroupId(lesson.group_id);
        setCurrentWeek(parseISO(lesson.date));
        if (lesson.subject_id) {
          setSelectedSubjectId(lesson.subject_id);
        }
        setInitialLoadDone(true);
      }
    } catch {
      console.error('Ошибка загрузки занятия');
      setInitialLoadDone(true);
    }
  };

  useEffect(() => {
    loadGroups();
    loadSubjects();
  }, []);

  useEffect(() => {
    if (selectedGroupId && (initialLoadDone || !lessonIdParam)) {
      loadJournalData();
    }
  }, [selectedGroupId, selectedSubjectId, selectedLessonType, currentWeek, attestationPeriod, initialLoadDone]);

  const loadGroups = async () => {
    try {
      const { data } = await api.get('/groups/');
      setGroups(data);
      if (data.length > 0 && !selectedGroupId) {
        setSelectedGroupId(data[0].id);
      }
    } catch {
      console.error('Ошибка загрузки групп');
    } finally {
      setIsLoading(false);
    }
  };

  const loadSubjects = async () => {
    try {
      const { data } = await api.get('/admin/subjects/');
      setSubjects(data);
    } catch {
      console.error('Ошибка загрузки предметов');
    }
  };

  const loadJournalData = useCallback(async () => {
    if (!selectedGroupId) return;
    setIsLoading(true);
    
    try {
      // Determine date range based on attestation period or week
      let startDate: string;
      let endDate: string;
      
      if (attestationPeriod !== 'all') {
        const periodDates = getAttestationPeriodDates(attestationPeriod, getSemesterStart());
        if (periodDates) {
          startDate = format(periodDates.start, 'yyyy-MM-dd');
          endDate = format(periodDates.end, 'yyyy-MM-dd');
        } else {
          startDate = format(weekStart, 'yyyy-MM-dd');
          endDate = format(weekEnd, 'yyyy-MM-dd');
        }
      } else {
        startDate = format(weekStart, 'yyyy-MM-dd');
        endDate = format(weekEnd, 'yyyy-MM-dd');
      }
      
      const params: Record<string, string> = {
        group_id: selectedGroupId,
        start_date: startDate,
        end_date: endDate,
      };
      if (selectedSubjectId !== 'all') params.subject_id = selectedSubjectId;
      if (selectedLessonType !== 'all') params.lesson_type = selectedLessonType;

      const { data: lessonsData } = await api.get('/admin/journal/lessons', { params });
      setLessons(lessonsData);

      const { data: groupData } = await api.get(`/groups/${selectedGroupId}`);
      setStudents(groupData.students || []);

      // Load attestation scores if period is selected
      if (attestationPeriod !== 'all') {
        try {
          const attestationData = await AttestationAPI.calculateGroup(
            selectedGroupId, 
            attestationPeriod as AttestationType
          );
          const scoresMap: Record<string, AttestationResult> = {};
          for (const student of attestationData.students) {
            scoresMap[student.student_id] = student;
          }
          setAttestationScores(scoresMap);
        } catch (err) {
          console.error('Ошибка загрузки баллов аттестации', err);
          setAttestationScores({});
        }
      } else {
        setAttestationScores({});
      }

      if (lessonsData.length > 0) {
        const lessonIds = lessonsData.map((l: Lesson) => l.id);
        
        const [attendanceRes, gradesRes, statsRes] = await Promise.all([
          api.get('/admin/journal/attendance', { params: { group_id: selectedGroupId, lesson_ids: lessonIds } }),
          api.get('/admin/journal/grades', { params: { lesson_ids: lessonIds } }),
          api.get('/admin/journal/stats', { 
            params: { 
              group_id: selectedGroupId,
              start_date: startDate,
              end_date: endDate,
              ...(selectedSubjectId !== 'all' && { subject_id: selectedSubjectId })
            } 
          }),
        ]);

        const attMap: Record<string, Record<string, string>> = {};
        for (const a of attendanceRes.data) {
          if (!attMap[a.lesson_id]) attMap[a.lesson_id] = {};
          attMap[a.lesson_id][a.student_id] = a.status;
        }
        setAttendance(attMap);

        const gradeMap: Record<string, Record<string, GradeData>> = {};
        for (const g of gradesRes.data) {
          if (!gradeMap[g.lesson_id]) gradeMap[g.lesson_id] = {};
          gradeMap[g.lesson_id][g.student_id] = { grade: g.grade, work_number: g.work_number };
        }
        setGrades(gradeMap);
        setStats(statsRes.data);
      } else {
        setAttendance({});
        setGrades({});
        setStats(null);
      }
    } catch (err) {
      console.error('Ошибка загрузки данных журнала', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedGroupId, selectedSubjectId, selectedLessonType, weekStart, weekEnd, attestationPeriod]);

  const refetchStats = useCallback(async () => {
    if (!selectedGroupId || lessons.length === 0) return;
    try {
      const { data } = await api.get('/admin/journal/stats', {
        params: {
          group_id: selectedGroupId,
          start_date: format(weekStart, 'yyyy-MM-dd'),
          end_date: format(weekEnd, 'yyyy-MM-dd'),
          ...(selectedSubjectId !== 'all' && { subject_id: selectedSubjectId })
        }
      });
      setStats(data);
    } catch {
      console.error('Ошибка обновления статистики');
    }
  }, [selectedGroupId, selectedSubjectId, weekStart, weekEnd, lessons.length]);

  const updateAttendance = async (lessonId: string, studentId: string, status: string) => {
    try {
      await api.post('/admin/journal/attendance/bulk', {
        lesson_id: lessonId,
        records: [{ student_id: studentId, status }]
      });
      setAttendance(prev => ({
        ...prev,
        [lessonId]: { ...prev[lessonId], [studentId]: status }
      }));
      // Refetch stats after attendance change
      await refetchStats();
    } catch {
      console.error('Ошибка обновления посещаемости');
    }
  };

  const updateGrade = async (lessonId: string, studentId: string, grade: number, workNumber: number | null = null) => {
    try {
      await api.post('/admin/journal/grades', {
        lesson_id: lessonId,
        student_id: studentId,
        grade,
        work_number: workNumber
      });
      setGrades(prev => ({
        ...prev,
        [lessonId]: { ...prev[lessonId], [studentId]: { grade, work_number: workNumber } }
      }));
      const currentStatus = attendance[lessonId]?.[studentId];
      if (!currentStatus || currentStatus === 'ABSENT') {
        await updateAttendance(lessonId, studentId, 'PRESENT');
      } else {
        // Refetch stats after grade change (if attendance wasn't updated)
        await refetchStats();
      }
    } catch {
      console.error('Ошибка обновления оценки');
    }
  };

  return {
    groups,
    subjects,
    selectedGroupId,
    setSelectedGroupId,
    selectedSubjectId,
    setSelectedSubjectId,
    selectedLessonType,
    setSelectedLessonType,
    currentWeek,
    setCurrentWeek,
    attestationPeriod,
    setAttestationPeriod,
    lessons,
    students,
    attendance,
    grades,
    attestationScores,
    stats,
    isLoading,
    updateAttendance,
    updateGrade,
  };
}
