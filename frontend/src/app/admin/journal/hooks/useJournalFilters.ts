'use client';

import { useState, useEffect } from 'react';
import { startOfWeek, endOfWeek } from 'date-fns';
import { SEMESTER_MONTHS, SEMESTER_DETECTION } from '@/lib/academic-constants';

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
}

// Helper to detect current semester
function detectCurrentSemester(): SemesterInfo {
  const now = new Date();
  if (now.getMonth() >= SEMESTER_DETECTION.fallStartMonth) { // сентябрь-декабрь
    return { academicYear: now.getFullYear(), semester: 1 };
  } else if (now.getMonth() <= SEMESTER_DETECTION.springEndMonth) { // январь-май
    return { academicYear: now.getFullYear() - 1, semester: 2 };
  } else { // июнь-август
    return { academicYear: now.getFullYear() - 1, semester: 2 };
  }
}

// Get semester date range
export function getSemesterDates(sem: SemesterInfo): { start: Date; end: Date } {
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
  const [selectedGroupId, setSelectedGroupId] = useState<string>('');
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('all');
  const [selectedLessonType, setSelectedLessonType] = useState<string>('all');
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const [attestationPeriod, setAttestationPeriod] = useState<AttestationPeriod>('all');
  const [selectedSemester, setSelectedSemester] = useState<SemesterInfo>(detectCurrentSemester);

  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(currentWeek, { weekStartsOn: 1 });

  // Semester start for attestation periods
  const getSemesterStart = () => {
    const dates = getSemesterDates(selectedSemester);
    return dates.start;
  };

  // Reset week to semester start when semester changes
  useEffect(() => {
    const semDates = getSemesterDates(selectedSemester);
    if (currentWeek < semDates.start || currentWeek > semDates.end) {
      setCurrentWeek(semDates.start);
    }
  }, [selectedSemester]);

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
    getSemesterDates,
    getSemesterStart,
  };
}
