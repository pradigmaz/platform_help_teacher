'use client';
'use no memo';

import { useState, useEffect } from 'react';
import { startOfWeek, endOfWeek } from 'date-fns';
import { SEMESTER_MONTHS } from '@/lib/academic-constants';
import { useSemesterInfo, getSemesterDates as getSemesterDatesFromHook } from '@/hooks/useSemesterInfo';

// Attestation period type
export type AttestationPeriod = 'all' | 'first' | 'second';

// Semester type
export type SemesterInfo = {
  academicYear: number;
  semester: 1 | 2;
};

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
  semesterLoading: boolean;
}

/**
 * Get semester date range.
 * Использует semester_start_date если доступен, иначе fallback на константы.
 */
export function getSemesterDates(
  sem: SemesterInfo, 
  semesterStartDate?: string | null
): { start: Date; end: Date } {
  // Если есть semester_start_date из API - используем его
  if (semesterStartDate) {
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
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const [attestationPeriod, setAttestationPeriod] = useState<AttestationPeriod>('all');
  const [selectedSemester, setSelectedSemester] = useState<SemesterInfo>({
    academicYear,
    semester,
  });

  // Обновляем selectedSemester когда данные загрузятся из API
  useEffect(() => {
    if (!semesterLoading) {
      setSelectedSemester({ academicYear, semester });
    }
  }, [academicYear, semester, semesterLoading]);

  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(currentWeek, { weekStartsOn: 1 });

  // Обёртка для getSemesterDates с учётом semesterStartDate
  const getSemesterDatesWithApi = (sem: SemesterInfo) => {
    return getSemesterDates(sem, semesterStartDate);
  };

  // Semester start for attestation periods
  const getSemesterStart = () => {
    const dates = getSemesterDatesWithApi(selectedSemester);
    return dates.start;
  };

  // Reset week to semester start when semester changes
  useEffect(() => {
    const semDates = getSemesterDatesWithApi(selectedSemester);
    if (currentWeek < semDates.start || currentWeek > semDates.end) {
      setCurrentWeek(semDates.start);
    }
  }, [selectedSemester, semesterStartDate]);

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
    semesterLoading,
  };
}
