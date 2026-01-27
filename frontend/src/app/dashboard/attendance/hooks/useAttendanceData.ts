import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { StudentAPI, type AttendanceRecord, type StudentAttendance } from '@/lib/api';
import type { AttendanceMap, AttendanceRecordsByDate, NormalizedStats } from '../types';

export type UseAttendanceDataResult = {
  loading: boolean;
  attendance: StudentAttendance | null;
  error: string | null;
  stats: NormalizedStats;
  attendanceMap: AttendanceMap;
  recordsByDate: AttendanceRecordsByDate;
  reload: () => Promise<void>;
};

export function useAttendanceData(): UseAttendanceDataResult {
  const [loading, setLoading] = useState(true);
  const [attendance, setAttendance] = useState<StudentAttendance | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadAttendance = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await StudentAPI.getAttendance();
      setAttendance(data);
    } catch (err) {
      console.error('Attendance fetch failed', err);
      setError('Не удалось загрузить посещаемость');
      toast.error('Ошибка загрузки посещаемости');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAttendance();
  }, [loadAttendance]);

  const attendanceMap = useMemo(() => buildAttendanceMap(attendance?.records), [attendance?.records]);
  const recordsByDate = useMemo(() => groupRecordsByDate(attendance?.records), [attendance?.records]);
  const stats = useMemo(() => normalizeStats(attendance?.stats), [attendance?.stats]);

  return {
    loading,
    attendance,
    error,
    stats,
    attendanceMap,
    recordsByDate,
    reload: loadAttendance,
  };
}

function normalizeStats(stats?: StudentAttendance['stats']): NormalizedStats {
  return {
    total_classes: stats?.total_classes ?? 0,
    attendance_rate: stats?.attendance_rate ?? 0,
    present: stats?.present ?? 0,
    late: stats?.late ?? 0,
    excused: stats?.excused ?? 0,
    absent: stats?.absent ?? 0,
  };
}

function buildAttendanceMap(records?: AttendanceRecord[]): AttendanceMap {
  return (records ?? []).reduce<AttendanceMap>((map, record) => {
    if (record?.date && !map[record.date]) {
      map[record.date] = record.status as AttendanceMap[keyof AttendanceMap];
    }
    return map;
  }, {});
}

function groupRecordsByDate(records?: AttendanceRecord[]): AttendanceRecordsByDate {
  if (!records) return [];

  const grouped = records.reduce<Record<string, AttendanceRecord[]>>((acc, record) => {
    if (!record.date) return acc;
    if (!acc[record.date]) acc[record.date] = [];
    acc[record.date].push(record);
    return acc;
  }, {});

  return Object.entries(grouped)
    .sort(([a], [b]) => b.localeCompare(a))
    .slice(0, 20);
}
