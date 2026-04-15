'use client';
'use no memo';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { startOfWeek, addDays, getDay, addWeeks } from 'date-fns';
import { SEMESTER_MONTHS } from '@/lib/academic-constants';
import { useSemesterInfo, getSemesterDates as getSemesterDatesFromHook } from '@/hooks/useSemesterInfo';

// В воскресенье показываем следующую неделю (как в расписании)
function getInitialWeek(): Date {
  const today = new Date();
  return getDay(today) === 0 ? addWeeks(today, 1) : today;
}

// Attestation period type
export type AttestationPeriod = 'all' | 'first' | 'second';

// Semester type
export type SemesterInfo = {
  academicYear: number;
  semester: 1 | 2;
};

export function sameSemesterInfo(left: SemesterInfo, right: SemesterInfo): boolean {
  return left.academicYear === right.academicYear && left.semester === right.semester;
}

export interface UseJournalFiltersReturn {
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
  weekStart: Date;
  weekEnd: Date;
  getSemesterDates: (sem: SemesterInfo) => { start: Date; end: Date };
  getSemesterStart: () => Date;
  isCurrentSemesterSelected: boolean;
  semesterLoading: boolean;
}

/**
 * Get semester date range.
 * Использует semester_start_date если доступен, иначе fallback на константы.
 */
export function getSemesterDates(
  sem: SemesterInfo, 
  semesterStartDate?: string | null,
  currentSemester?: SemesterInfo,
): { start: Date; end: Date } {
  const isCurrentSemester =
    currentSemester?.academicYear === sem.academicYear &&
    currentSemester?.semester === sem.semester;

  // Если есть semester_start_date из API - используем его только для текущего семестра
  if (semesterStartDate && isCurrentSemester) {
    return getSemesterDatesFromHook(sem.academicYear, sem.semester, semesterStartDate);
  }
  
  // Fallback на константы
  if (sem.semester === 1) {
    return {
      start: new Date(sem.academicYear, SEMESTER_MONTHS.fall.startMonth, SEMESTER_MONTHS.fall.startDay),
      end: new Date(sem.academicYear, SEMESTER_MONTHS.fall.endMonth, SEMESTER_MONTHS.fall.endDay),
    };
  } else {
    return {
      start: new Date(sem.academicYear + 1, SEMESTER_MONTHS.spring.startMonth, SEMESTER_MONTHS.spring.startDay),
      end: new Date(sem.academicYear + 1, SEMESTER_MONTHS.spring.endMonth, SEMESTER_MONTHS.spring.endDay),
    };
  }
}

export function useJournalFilters(): UseJournalFiltersReturn {
  // Получаем семестр из API (с fallback на хардкод)
  const { academicYear, semester, semesterStartDate, loading: semesterLoading } = useSemesterInfo();
  
  const [selectedGroupId, setSelectedGroupId] = useState<string>('');
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('all');
  const [selectedLessonType, setSelectedLessonType] = useState<string>('all');
  const [currentWeek, setCurrentWeek] = useState(getInitialWeek);
  const [attestationPeriod, setAttestationPeriod] = useState<AttestationPeriod>('all');
  const [selectedSemester, setSelectedSemester] = useState<SemesterInfo>({
    academicYear,
    semester,
  });

  // Обновляем selectedSemester когда данные загрузятся из API
  useEffect(() => {
    if (!semesterLoading) {
      const nextSemester = { academicYear, semester } as SemesterInfo;
      setSelectedSemester((currentSemester) => (
        sameSemesterInfo(currentSemester, nextSemester) ? currentSemester : nextSemester
      ));
    }
  }, [academicYear, semester, semesterLoading]);

  const weekStart = useMemo(
    () => startOfWeek(currentWeek, { weekStartsOn: 1 }),
    [currentWeek],
  );
  // Суббота = Пн + 5 дней (как в расписании, без воскресенья)
  const weekEnd = useMemo(() => addDays(weekStart, 5), [weekStart]);
  const currentSemesterInfo = useMemo(() => ({ academicYear, semester }), [academicYear, semester]);
  const isCurrentSemesterSelected =
    selectedSemester.academicYear === academicYear && selectedSemester.semester === semester;

  // Обёртка для getSemesterDates с учётом semesterStartDate
  const getSemesterDatesWithApi = useCallback((sem: SemesterInfo) => {
    return getSemesterDates(sem, semesterStartDate, currentSemesterInfo);
  }, [currentSemesterInfo, semesterStartDate]);

  // Semester start for attestation periods
  const getSemesterStart = useCallback(() => {
    const dates = getSemesterDatesWithApi(selectedSemester);
    return dates.start;
  }, [getSemesterDatesWithApi, selectedSemester]);

  // Reset week to semester start when semester changes
  // Но только если текущая неделя реально вне семестра (не при первой загрузке)
  useEffect(() => {
    if (semesterLoading) return; // Ждём загрузки данных
    
    const semDates = getSemesterDatesWithApi(selectedSemester);
    const initialWeek = getInitialWeek();
    
    // Если initialWeek в пределах семестра — используем её
    if (initialWeek >= semDates.start && initialWeek <= semDates.end) {
      if (currentWeek < semDates.start || currentWeek > semDates.end) {
        setCurrentWeek(initialWeek);
      }
    } else if (currentWeek < semDates.start || currentWeek > semDates.end) {
      setCurrentWeek(semDates.start);
    }
  }, [currentWeek, getSemesterDatesWithApi, selectedSemester, semesterLoading]);

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
    weekStart,
    weekEnd,
    getSemesterDates: getSemesterDatesWithApi,
    getSemesterStart,
    isCurrentSemesterSelected,
    semesterLoading,
  };
}
