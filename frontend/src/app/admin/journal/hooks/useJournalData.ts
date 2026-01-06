'use client';

import { useState, useEffect, useCallback } from 'react';
import { format, startOfWeek, endOfWeek, parseISO, addWeeks, startOfYear } from 'date-fns';
import api, { AttestationAPI, AttestationType, AttestationResult } from '@/lib/api';
import type { Group, Subject, Lesson, Student, GradeData, JournalStats } from '../lib/journal-constants';

// Attestation period type
export type AttestationPeriod = 'all' | 'first' | 'second';

// Semester type
export type SemesterInfo = {
  academicYear: number;
  semester: 1 | 2;
};

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
  selectedSemester: SemesterInfo;
  setSelectedSemester: (semester: SemesterInfo) => void;
  lessons: Lesson[];
  students: Student[];
  attendance: Record<string, Record<string, string>>;
  grades: Record<string, Record<string, GradeData>>;
  attestationScores: Record<string, AttestationResult>;
  stats: JournalStats | null;
  isLoading: boolean;
  updateAttendance: (lessonId: string, studentId: string, status: string | null) => Promise<void>;
  updateGrade: (lessonId: string, studentId: string, grade: number | null, workNumber?: number | null) => Promise<void>;
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
  
  // Semester state - auto-detect current semester
  const [selectedSemester, setSelectedSemester] = useState<SemesterInfo>(() => {
    const now = new Date();
    if (now.getMonth() >= 8) { // сентябрь-декабрь
      return { academicYear: now.getFullYear(), semester: 1 };
    } else if (now.getMonth() <= 4) { // январь-май
      return { academicYear: now.getFullYear() - 1, semester: 2 };
    } else { // июнь-август
      return { academicYear: now.getFullYear() - 1, semester: 2 };
    }
  });

  // Get semester date range
  const getSemesterDates = (sem: SemesterInfo) => {
    if (sem.semester === 1) {
      return {
        start: new Date(sem.academicYear, 8, 1),  // 1 сентября
        end: new Date(sem.academicYear, 11, 31),  // 31 декабря
      };
    } else {
      return {
        start: new Date(sem.academicYear + 1, 0, 1),  // 1 января
        end: new Date(sem.academicYear + 1, 4, 31),   // 31 мая
      };
    }
  };

  // Semester start for attestation periods
  const getSemesterStart = () => {
    const dates = getSemesterDates(selectedSemester);
    return dates.start;
  };

  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(currentWeek, { weekStartsOn: 1 });

  // Reset week to semester start when semester changes
  useEffect(() => {
    const semDates = getSemesterDates(selectedSemester);
    // If current week is outside semester, jump to semester start
    if (currentWeek < semDates.start || currentWeek > semDates.end) {
      setCurrentWeek(semDates.start);
    }
  }, [selectedSemester]);

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
  }, [selectedGroupId, selectedSubjectId, selectedLessonType, currentWeek, attestationPeriod, selectedSemester, initialLoadDone]);

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

  // Load subjects for current semester based on lessons
  const loadSemesterSubjects = useCallback(async () => {
    if (!selectedGroupId) return;
    
    const semDates = getSemesterDates(selectedSemester);
    try {
      const { data: semesterLessons } = await api.get('/admin/journal/lessons', {
        params: {
          group_id: selectedGroupId,
          start_date: format(semDates.start, 'yyyy-MM-dd'),
          end_date: format(semDates.end, 'yyyy-MM-dd'),
        }
      });
      
      // Get unique subject IDs from semester lessons
      const subjectIds = new Set(
        semesterLessons.map((l: Lesson) => l.subject_id).filter(Boolean)
      );
      
      // Filter subjects
      const { data: allSubjects } = await api.get('/admin/subjects/');
      const filtered = allSubjects.filter((s: Subject) => subjectIds.has(s.id));
      setSubjects(filtered);
      
      // Reset subject selection if current subject not in semester
      if (selectedSubjectId !== 'all' && !subjectIds.has(selectedSubjectId)) {
        setSelectedSubjectId('all');
      }
    } catch {
      console.error('Ошибка загрузки предметов семестра');
    }
  }, [selectedGroupId, selectedSemester]);

  useEffect(() => {
    if (selectedGroupId) {
      loadSemesterSubjects();
    }
  }, [selectedGroupId, selectedSemester, loadSemesterSubjects]);

  const loadSubjects = async () => {
    // Now handled by loadSemesterSubjects
  };

  const loadJournalData = useCallback(async () => {
    if (!selectedGroupId) return;
    setIsLoading(true);
    
    try {
      // Get semester date boundaries
      const semesterDates = getSemesterDates(selectedSemester);
      
      // Determine date range based on attestation period or week
      let startDate: string;
      let endDate: string;
      
      if (attestationPeriod !== 'all') {
        const periodDates = getAttestationPeriodDates(attestationPeriod, getSemesterStart());
        if (periodDates) {
          startDate = format(periodDates.start, 'yyyy-MM-dd');
          endDate = format(periodDates.end, 'yyyy-MM-dd');
        } else {
          startDate = format(semesterDates.start, 'yyyy-MM-dd');
          endDate = format(semesterDates.end, 'yyyy-MM-dd');
        }
      } else {
        // Clamp week to semester boundaries
        const clampedWeekStart = weekStart < semesterDates.start ? semesterDates.start : weekStart;
        const clampedWeekEnd = weekEnd > semesterDates.end ? semesterDates.end : weekEnd;
        startDate = format(clampedWeekStart, 'yyyy-MM-dd');
        endDate = format(clampedWeekEnd, 'yyyy-MM-dd');
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

  const updateAttendance = async (lessonId: string, studentId: string, status: string | null) => {
    try {
      if (status === null) {
        // Delete attendance
        await api.delete('/admin/journal/attendance', { 
          params: { lesson_id: lessonId, student_id: studentId } 
        });
        setAttendance(prev => {
          const updated = { ...prev };
          if (updated[lessonId]) {
            delete updated[lessonId][studentId];
          }
          return updated;
        });
      } else {
        await api.post('/admin/journal/attendance/bulk', {
          lesson_id: lessonId,
          records: [{ student_id: studentId, status }]
        });
        setAttendance(prev => ({
          ...prev,
          [lessonId]: { ...prev[lessonId], [studentId]: status }
        }));
      }
      // Refetch stats after attendance change
      await refetchStats();
    } catch {
      console.error('Ошибка обновления посещаемости');
    }
  };

  const updateGrade = async (lessonId: string, studentId: string, grade: number | null, workNumber: number | null = null) => {
    try {
      if (grade === null) {
        // Delete grade
        await api.delete('/admin/journal/grades', { 
          params: { lesson_id: lessonId, student_id: studentId } 
        });
        setGrades(prev => {
          const updated = { ...prev };
          if (updated[lessonId]) {
            delete updated[lessonId][studentId];
          }
          return updated;
        });
        await refetchStats();
      } else {
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
    selectedSemester,
    setSelectedSemester,
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
