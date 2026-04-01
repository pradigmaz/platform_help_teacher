'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { format, parseISO } from 'date-fns';
import { toast } from 'sonner';
import api from '@/lib/api';
import { getAttestationPeriodDates as getBackendAttestationPeriodDates } from '@/lib/attestation-period';
import type { Group, Subject, Lesson, Student } from '../lib/journal-constants';
import { type AttestationPeriod, type SemesterInfo, getSemesterDates } from './useJournalFilters';

export interface UseJournalLessonsProps {
  selectedGroupId: string;
  selectedSubjectId: string;
  selectedLessonType: string;
  weekStart: Date;
  weekEnd: Date;
  attestationPeriod: AttestationPeriod;
  selectedSemester: SemesterInfo;
  getSemesterStart: () => Date;
  lessonIdParam: string | null;
  setSelectedGroupId: (id: string) => void;
  setSelectedSubjectId: (id: string) => void;
  setCurrentWeek: (date: Date) => void;
}

export interface UseJournalLessonsReturn {
  groups: Group[];
  subjects: Subject[];
  lessons: Lesson[];
  students: Student[];
  isLoading: boolean;
  initialLoadDone: boolean;
  startDate: string;
  endDate: string;
  refreshLessonsData: () => Promise<{
    lessons: Lesson[];
    students: Student[];
    startDate: string;
    endDate: string;
  } | null>;
}

// Helper to get attestation period date range
function getAttestationPeriodDates(period: AttestationPeriod, semesterStart: Date): { start: Date; end: Date } | null {
  if (period === 'all') return null;
  return getBackendAttestationPeriodDates(period, semesterStart);
}

export function useJournalLessons(props: UseJournalLessonsProps): UseJournalLessonsReturn {
  const {
    selectedGroupId, selectedSubjectId, selectedLessonType,
    weekStart, weekEnd, attestationPeriod, selectedSemester,
    getSemesterStart, lessonIdParam,
    setSelectedGroupId, setSelectedSubjectId, setCurrentWeek
  } = props;

  const [groups, setGroups] = useState<Group[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const selectedGroupIdRef = useRef(selectedGroupId);

  useEffect(() => {
    selectedGroupIdRef.current = selectedGroupId;
  }, [selectedGroupId]);

  const loadLessonById = useCallback(async (lessonId: string) => {
    try {
      const { data: lesson } = await api.get(`/admin/lessons/${lessonId}`);
      if (lesson) {
        setSelectedGroupId(lesson.group_id);
        setCurrentWeek(parseISO(lesson.date));
        if (lesson.subject_id) setSelectedSubjectId(lesson.subject_id);
        setInitialLoadDone(true);
      }
    } catch {
      toast.error('Ошибка загрузки занятия');
      setInitialLoadDone(true);
    }
  }, [setCurrentWeek, setSelectedGroupId, setSelectedSubjectId]);

  // Load lesson by ID from URL
  useEffect(() => {
    if (lessonIdParam && !initialLoadDone) {
      void loadLessonById(lessonIdParam);
    }
  }, [initialLoadDone, lessonIdParam, loadLessonById]);

  // Load groups on mount
  useEffect(() => {
    const loadGroups = async () => {
      try {
        const { data } = await api.get('/groups/');
        setGroups(data);
        if (data.length > 0 && !selectedGroupIdRef.current) {
          setSelectedGroupId(data[0].id);
        }
      } catch {
        toast.error('Ошибка загрузки групп');
      } finally {
        setIsLoading(false);
      }
    };

    void loadGroups();
  }, [setSelectedGroupId]);

  const loadSemesterSubjects = useCallback(async () => {
    if (!selectedGroupId) {
      return;
    }

    const semDates = getSemesterDates(selectedSemester);
    try {
      const { data: semesterLessons } = await api.get('/admin/journal/lessons', {
        params: {
          group_id: selectedGroupId,
          start_date: format(semDates.start, 'yyyy-MM-dd'),
          end_date: format(semDates.end, 'yyyy-MM-dd'),
        }
      });

      const subjectIds = new Set(
        semesterLessons.map((lesson: Lesson) => lesson.subject_id).filter(Boolean)
      );

      const { data: allSubjects } = await api.get('/admin/subjects/');
      const filtered = allSubjects.filter((subject: Subject) => subjectIds.has(subject.id));
      setSubjects(filtered);

      if (selectedSubjectId !== 'all' && !subjectIds.has(selectedSubjectId)) {
        setSelectedSubjectId('all');
      }
    } catch {
      toast.error('Ошибка загрузки предметов семестра');
    }
  }, [selectedGroupId, selectedSemester, selectedSubjectId, setSelectedSubjectId]);

  // Load subjects for current semester
  useEffect(() => {
    void loadSemesterSubjects();
  }, [loadSemesterSubjects]);

  const loadLessonsData = useCallback(async () => {
    if (!selectedGroupId) return null;
    setIsLoading(true);
    
    try {
      const semesterDates = getSemesterDates(selectedSemester);
      let start: string, end: string;
      
      if (attestationPeriod !== 'all') {
        const periodDates = getAttestationPeriodDates(attestationPeriod, getSemesterStart());
        if (periodDates) {
          start = format(periodDates.start, 'yyyy-MM-dd');
          end = format(periodDates.end, 'yyyy-MM-dd');
        } else {
          start = format(semesterDates.start, 'yyyy-MM-dd');
          end = format(semesterDates.end, 'yyyy-MM-dd');
        }
      } else {
        const clampedStart = weekStart < semesterDates.start ? semesterDates.start : weekStart;
        const clampedEnd = weekEnd > semesterDates.end ? semesterDates.end : weekEnd;
        start = format(clampedStart, 'yyyy-MM-dd');
        end = format(clampedEnd, 'yyyy-MM-dd');
      }
      
      setStartDate(start);
      setEndDate(end);

      const params: Record<string, string> = {
        group_id: selectedGroupId,
        start_date: start,
        end_date: end,
      };
      if (selectedSubjectId !== 'all') params.subject_id = selectedSubjectId;
      if (selectedLessonType !== 'all') params.lesson_type = selectedLessonType;

      const { data: lessonsData } = await api.get('/admin/journal/lessons', { params });
      setLessons(lessonsData);

      const { data: groupData } = await api.get(`/groups/${selectedGroupId}`);
      setStudents(groupData.students || []);
      return {
        lessons: lessonsData,
        students: groupData.students || [],
        startDate: start,
        endDate: end,
      };
    } catch {
      toast.error('Ошибка загрузки занятий');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [
    attestationPeriod,
    getSemesterStart,
    selectedGroupId,
    selectedLessonType,
    selectedSemester,
    selectedSubjectId,
    weekEnd,
    weekStart,
  ]);

  // Load lessons and students
  useEffect(() => {
    if (selectedGroupId && (initialLoadDone || !lessonIdParam)) {
      void loadLessonsData();
    }
  }, [initialLoadDone, lessonIdParam, loadLessonsData, selectedGroupId]);

  return {
    groups,
    subjects,
    lessons,
    students,
    isLoading,
    initialLoadDone,
    startDate,
    endDate,
    refreshLessonsData: loadLessonsData,
  };
}
