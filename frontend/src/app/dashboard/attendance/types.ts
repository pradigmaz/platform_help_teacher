import { IconBook, IconFlask, IconSchool } from '@tabler/icons-react';
import type { AttendanceRecord } from '@/lib/api';

export type AttendanceStatus = 'PRESENT' | 'LATE' | 'EXCUSED' | 'ABSENT';

export type AttendanceMap = Record<string, AttendanceStatus>;

export type CalendarDay = {
  date: number;
  isCurrentMonth: boolean;
  dateStr?: string;
  isToday?: boolean;
};

export type NormalizedStats = {
  total_classes: number;
  attendance_rate: number;
  present: number;
  late: number;
  excused: number;
  absent: number;
};

export type AttendanceRecordsByDate = Array<[string, AttendanceRecord[]]>;

export const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

export const MONTHS = [
  'Январь',
  'Февраль',
  'Март',
  'Апрель',
  'Май',
  'Июнь',
  'Июль',
  'Август',
  'Сентябрь',
  'Октябрь',
  'Ноябрь',
  'Декабрь',
];

export const STATUS_COLORS: Record<AttendanceStatus, string> = {
  PRESENT: 'bg-green-500 text-white',
  LATE: 'bg-yellow-500 text-white',
  EXCUSED: 'bg-blue-500 text-white',
  ABSENT: 'bg-red-500 text-white',
};

export const STATUS_LABELS: Record<AttendanceStatus, string> = {
  PRESENT: 'Присутствовал',
  LATE: 'Опоздание',
  EXCUSED: 'Уваж. причина',
  ABSENT: 'Пропуск',
};

export const LESSON_TYPE_LABELS: Record<string, { label: string; icon: typeof IconBook }> = {
  lecture: { label: 'Лекция', icon: IconBook },
  practice: { label: 'Практика', icon: IconSchool },
  lab: { label: 'Лаба', icon: IconFlask },
};

export function toDateKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return dateStr;

  const day = date.getDate();
  const month = MONTHS[date.getMonth()];
  const weekday = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'][date.getDay()];
  return `${weekday}, ${day} ${month.toLowerCase().slice(0, 3)}`;
}
