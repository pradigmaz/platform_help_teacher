'use client';

import { useState, useEffect, useCallback } from 'react';
import { format, parseISO, addWeeks } from 'date-fns';
import { toast } from 'sonner';
import api from '@/lib/api';
import { ATTESTATION_WEEKS } from '@/lib/academic-constants';
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
}

// Helper to get attestation period date range
function getAttestationPeriodDates(period: AttestationPeriod, semesterStart: Date): { start: Date; end: Date } | null {
  if (period === 'all') return null;
  
  if (period === 'first') {
    return { start: semesterStart, end: addWeeks(semesterStart, ATTESTATION_WEEKS.first) };
  } else {
    return { start: addWeeks(semesterStart, ATTESTATION_WEEKS.first), end: addWeeks(semesterStart, ATTESTATION_WEEKS.second) };
  }
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
        if (lesson.subject_id) setSelectedSubjectId(lesson.subject_id);
        setInitialLoadDone(true);
      }
    } catch {
      toast.error('Ошибка загрузки занятия');
      setInitialLoadDone(true);
    }
  };

  // Load groups on mount
  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    try {
      const { data } = await api.get('/groups/');
      setGroups(data);
      if (data.length > 0 && !selectedGroupId) {
        setSelectedGroupId(data[0].id);
      }
    } catch {
      toast.error('Ошибка загрузки групп');
    } finally {
      setIsLoading(false);
    }
  };

  // Stable keys for dependencies
  const semesterKey = `${selectedSemester.academicYear}-${selectedSemester.semester}`;
  const weekKey = `${format(weekStart, 'yyyy-MM-dd')}-${format(weekEnd, 'yyyy-MM-dd')}`;

  // Load subjects for current semester
  useEffect(() => {
    if (!selectedGroupId) return;
    
    const loadSemesterSubjects = async () => {
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
          semesterLessons.map((l: Lesson) => l.subject_id).filter(Boolean)
        );
        
        const { data: allSubjects } = await api.get('/admin/subjects/');
        const filtered = allSubjects.filter((s: Subject) => subjectIds.has(s.id));
        setSubjects(filtered);
        
        if (selectedSubjectId !== 'all' && !subjectIds.has(selectedSubjectId)) {
          setSelectedSubjectId('all');
        }
      } catch {
        toast.error('Ошибка загрузки предметов семестра');
      }
    };
    
    loadSemesterSubjects();
  }, [selectedGroupId, semesterKey]);

  // Load lessons and students
  useEffect(() => {
    if (selectedGroupId && (initialLoadDone || !lessonIdParam)) {
      loadLessonsData();
    }
  }, [selectedGroupId, selectedSubjectId, selectedLessonType, weekKey, attestationPeriod, semesterKey, initialLoadDone]);

  const loadLessonsData = useCallback(async () => {
    if (!selectedGroupId) return;
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
    } catch (err) {
      toast.error('Ошибка загрузки занятий');
    } finally {
      setIsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedGroupId, selectedSubjectId, selectedLessonType, weekKey, attestationPeriod, semesterKey]);

  return {
    groups,
    subjects,
    lessons,
    students,
    isLoading,
    initialLoadDone,
    startDate,
    endDate,
  };
}
