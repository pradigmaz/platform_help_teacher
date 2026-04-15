'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api/client';
import { loadCached } from '@/lib/api/read-cache';

export interface SemesterInfo {
  semesterStartDate: string | null;
  academicYear: number;
  semester: 1 | 2;
}

export function getCurrentSemesterInfo(now: Date = new Date()): Pick<SemesterInfo, 'academicYear' | 'semester'> {
  const month = now.getMonth();
  const year = now.getFullYear();
  const semester = month >= 8 ? 1 : 2;
  return {
    academicYear: semester === 1 ? year : year - 1,
    semester,
  };
}

const currentSemesterInfo = getCurrentSemesterInfo();

const DEFAULT_SEMESTER_INFO: SemesterInfo = {
  semesterStartDate: null,
  academicYear: currentSemesterInfo.academicYear,
  semester: currentSemesterInfo.semester,
};

let cachedSemesterInfo: SemesterInfo | null = null;
let inFlightSemesterInfo: Promise<SemesterInfo> | null = null;

async function fetchSemesterInfo(): Promise<SemesterInfo> {
  if (!inFlightSemesterInfo) {
    inFlightSemesterInfo = loadCached(
      'public:semester-info',
      async () => {
        const response = await api.get('/public/semester-info');
        const data = response.data;
        return {
          semesterStartDate: data.semester_start_date,
          academicYear: data.academic_year,
          semester: data.semester as 1 | 2,
        };
      },
      {
        ttlMs: 30_000,
      },
    ).finally(() => {
      inFlightSemesterInfo = null;
    });
  }

  return inFlightSemesterInfo;
}

export function useSemesterInfo() {
  const [info, setInfo] = useState<SemesterInfo>(cachedSemesterInfo || DEFAULT_SEMESTER_INFO);
  const [loading, setLoading] = useState(!cachedSemesterInfo);

  useEffect(() => {
    if (cachedSemesterInfo) return;

    const fetchInfo = async () => {
      try {
        const semesterInfo = await fetchSemesterInfo();
        cachedSemesterInfo = semesterInfo;
        setInfo(semesterInfo);
      } catch {
        const fallbackSemesterInfo = getCurrentSemesterInfo();
        const fallback: SemesterInfo = {
          semesterStartDate: null,
          academicYear: fallbackSemesterInfo.academicYear,
          semester: fallbackSemesterInfo.semester,
        };
        setInfo(fallback);
      } finally {
        setLoading(false);
      }
    };

    fetchInfo();
  }, []);

  return { ...info, loading };
}

export function getSemesterDates(academicYear: number, semester: 1 | 2, semesterStartDate?: string | null) {
  if (semesterStartDate) {
    const start = new Date(semesterStartDate);
    // Семестр ~14 недель
    const end = new Date(start);
    end.setDate(start.getDate() + 14 * 7);
    return { start, end };
  }
  
  // Fallback на стандартные даты
  if (semester === 1) {
    return {
      start: new Date(academicYear, 8, 1), // 1 сентября
      end: new Date(academicYear, 11, 31), // 31 декабря
    };
  }
  return {
    start: new Date(academicYear + 1, 0, 1), // 1 января
    end: new Date(academicYear + 1, 4, 31), // 31 мая
  };
}
