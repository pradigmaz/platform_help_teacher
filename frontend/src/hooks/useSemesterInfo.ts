'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api/client';

export interface SemesterInfo {
  semesterStartDate: string | null;
  academicYear: number;
  semester: 1 | 2;
}

const DEFAULT_SEMESTER_INFO: SemesterInfo = {
  semesterStartDate: null,
  academicYear: new Date().getFullYear(),
  semester: new Date().getMonth() >= 8 ? 1 : 2,
};

let cachedSemesterInfo: SemesterInfo | null = null;

export function useSemesterInfo() {
  const [info, setInfo] = useState<SemesterInfo>(cachedSemesterInfo || DEFAULT_SEMESTER_INFO);
  const [loading, setLoading] = useState(!cachedSemesterInfo);

  useEffect(() => {
    if (cachedSemesterInfo) return;

    const fetchInfo = async () => {
      try {
        const response = await api.get('/semester-info');
        const data = response.data;
        const semesterInfo: SemesterInfo = {
          semesterStartDate: data.semester_start_date,
          academicYear: data.academic_year,
          semester: data.semester as 1 | 2,
        };
        cachedSemesterInfo = semesterInfo;
        setInfo(semesterInfo);
      } catch {
        // Fallback на хардкод если API недоступен
        const now = new Date();
        const fallback: SemesterInfo = {
          semesterStartDate: null,
          academicYear: now.getMonth() >= 8 ? now.getFullYear() : now.getFullYear() - 1,
          semester: now.getMonth() >= 8 || now.getMonth() <= 4 ? (now.getMonth() >= 8 ? 1 : 2) : 2,
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
