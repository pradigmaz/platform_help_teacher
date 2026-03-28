'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { format } from 'date-fns';
import { JournalAPI } from '@/lib/api';
import type { GroupResponse, JournalViewResponse, StudentInGroup } from '@/lib/api';
import type { Lesson, Subject, Student, JournalStats as JournalStatsType } from '../lib/journal-constants';
import { useJournalFilters, type AttestationPeriod, type SemesterInfo } from './useJournalFilters';
import { useJournalAttendance } from './useJournalAttendance';
import { useJournalGrades } from './useJournalGrades';
import { toast } from 'sonner';

export type { AttestationPeriod, SemesterInfo };

interface UseJournalDataProps {
  lessonIdParam: string | null;
}

function parseDateOnly(value: string): Date {
  return new Date(`${value}T00:00:00`);
}

function mapGroups(groups: GroupResponse[]) {
  return groups.map((group) => ({
    id: group.id,
    name: group.name,
  }));
}

function mapSubjects(subjects: JournalViewResponse['subjects']): Subject[] {
  return subjects.map((subject) => ({
    id: subject.id,
    name: subject.name,
  }));
}

function mapStudents(students: StudentInGroup[]): Student[] {
  return students.map((student) => ({
    id: student.id,
    full_name: student.full_name,
    subgroup: student.subgroup ?? null,
  }));
}

function mapLessons(lessons: JournalViewResponse['lessons']): Lesson[] {
  return lessons.map((lesson) => ({
    id: lesson.id,
    date: lesson.date,
    lesson_number: lesson.lesson_number,
    lesson_type: lesson.lesson_type,
    topic: lesson.topic,
    work_number: lesson.work_number,
    lecture_work_type: lesson.lecture_work_type,
    subgroup: lesson.subgroup,
    is_cancelled: lesson.is_cancelled,
    subject_id: lesson.subject_id,
    subject_name: lesson.subject_name,
  }));
}

export function useJournalData({ lessonIdParam }: UseJournalDataProps) {
  const filters = useJournalFilters();
  const {
    attestationPeriod,
    currentWeek,
    getSemesterStart,
    isCurrentSemesterSelected,
    selectedGroupId,
    selectedLessonType,
    selectedSemester,
    selectedSubjectId,
    semesterLoading,
    setCurrentWeek,
    setSelectedGroupId,
    setSelectedLessonType,
    setSelectedSemester,
    setSelectedSubjectId,
    setAttestationPeriod,
    weekEnd,
    weekStart,
  } = filters;
  const [groups, setGroups] = useState<ReturnType<typeof mapGroups>>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [stats, setStats] = useState<JournalStatsType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const skipNextLoadRef = useRef(false);
  const loadViewRef = useRef<(() => Promise<void>) | null>(null);
  const handleStatsRefetch = useCallback(() => {
    void loadViewRef.current?.();
  }, []);

  const attendanceHook = useJournalAttendance({ onStatsRefetch: handleStatsRefetch });
  const {
    attendance,
    isSaving: isAttendanceSaving,
    setAttendance,
    updateAttendance,
  } = attendanceHook;

  const gradesHook = useJournalGrades({ onStatsRefetch: handleStatsRefetch });
  const {
    attestationScores,
    grades,
    isSaving: isGradesSaving,
    setAttestationScores,
    setGrades,
    updateGrade,
  } = gradesHook;

  const loadView = useCallback(async () => {
    if (semesterLoading) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await JournalAPI.getView({
        group_id: selectedGroupId || undefined,
        subject_id: selectedSubjectId !== 'all' ? selectedSubjectId : undefined,
        lesson_type: selectedLessonType !== 'all' ? selectedLessonType : undefined,
        week_start: format(weekStart, 'yyyy-MM-dd'),
        week_end: format(weekEnd, 'yyyy-MM-dd'),
        attestation_period: attestationPeriod,
        academic_year: selectedSemester.academicYear,
        semester: selectedSemester.semester,
        semester_start_date: format(getSemesterStart(), 'yyyy-MM-dd'),
        lesson_id: lessonIdParam,
        include_attestation_scores:
          attestationPeriod !== 'all' &&
          selectedSubjectId !== 'all' &&
          isCurrentSemesterSelected,
      });

      setGroups(mapGroups(response.groups));
      setSubjects(mapSubjects(response.subjects));
      setLessons(mapLessons(response.lessons));
      setStudents(mapStudents(response.students));
      setAttendance(response.attendance);
      setGrades(response.grades);
      setAttestationScores(response.attestation_scores);
      setStats(response.stats);

      const resolvedGroupId = response.resolved.group_id ?? '';
      const resolvedSubjectId = response.resolved.subject_id ?? 'all';
      const resolvedWeekStart = response.resolved.week_start;
      const shouldSyncGroup = resolvedGroupId !== selectedGroupId;
      const shouldSyncSubject = resolvedSubjectId !== selectedSubjectId;
      const shouldSyncWeek =
        attestationPeriod === 'all' &&
        format(weekStart, 'yyyy-MM-dd') !== resolvedWeekStart;

      if (shouldSyncGroup || shouldSyncSubject || shouldSyncWeek) {
        skipNextLoadRef.current = true;
        if (shouldSyncGroup) {
          setSelectedGroupId(resolvedGroupId);
        }
        if (shouldSyncSubject) {
          setSelectedSubjectId(resolvedSubjectId);
        }
        if (shouldSyncWeek) {
          setCurrentWeek(parseDateOnly(resolvedWeekStart));
        }
      }
    } catch (error) {
      console.error('Failed to load journal view:', error);
      toast.error(error instanceof Error ? error.message : 'Ошибка загрузки журнала');
    } finally {
      setIsLoading(false);
    }
  }, [
    attestationPeriod,
    getSemesterStart,
    isCurrentSemesterSelected,
    lessonIdParam,
    selectedGroupId,
    selectedLessonType,
    selectedSemester,
    selectedSubjectId,
    semesterLoading,
    setCurrentWeek,
    setSelectedGroupId,
    setSelectedSubjectId,
    setAttendance,
    setAttestationScores,
    weekEnd,
    weekStart,
    setGrades,
  ]);

  useEffect(() => {
    loadViewRef.current = loadView;
  }, [loadView]);

  useEffect(() => {
    if (semesterLoading) {
      return;
    }

    if (skipNextLoadRef.current) {
      skipNextLoadRef.current = false;
      return;
    }

    void loadView();
  }, [
    attestationPeriod,
    currentWeek,
    loadView,
    selectedGroupId,
    selectedLessonType,
    selectedSemester,
    selectedSubjectId,
    semesterLoading,
  ]);

  return {
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
    isCurrentSemesterSelected,
    groups,
    subjects,
    lessons,
    students,
    isLoading,
    attendance,
    updateAttendance,
    grades,
    attestationScores,
    updateGrade,
    stats,
    refreshJournalData: loadView,
    isSaving: isAttendanceSaving || isGradesSaving,
  };
}
