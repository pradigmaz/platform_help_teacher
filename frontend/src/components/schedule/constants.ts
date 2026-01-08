import { Check, Clock, HelpCircle, XCircle } from 'lucide-react';
import type { AttendanceStatus } from './types';

export const LESSON_TIMES = [
  '08:00–09:30', '09:40–11:10', '11:20–12:50', '13:20–14:50',
  '15:00–16:30', '16:40–18:10', '18:20–19:50', '20:00–21:30'
];

export const TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  lecture: { label: 'Лекция', color: 'bg-blue-500/15 text-blue-400 border-blue-500/20' },
  lab: { label: 'Лаб. работа', color: 'bg-purple-500/15 text-purple-400 border-purple-500/20' },
  practice: { label: 'Практика', color: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20' },
};

export const ATTENDANCE_CONFIG: Record<AttendanceStatus, { 
  icon: typeof Check; 
  color: string; 
  bg: string; 
  label: string 
}> = {
  PRESENT: { icon: Check, color: 'text-emerald-500', bg: 'bg-emerald-500/15', label: 'Присутствует' },
  LATE: { icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-500/15', label: 'Опоздал' },
  EXCUSED: { icon: HelpCircle, color: 'text-blue-500', bg: 'bg-blue-500/15', label: 'Уваж. причина' },
  ABSENT: { icon: XCircle, color: 'text-rose-500', bg: 'bg-rose-500/15', label: 'Отсутствует' },
};

export const ATTENDANCE_CYCLE: AttendanceStatus[] = ['PRESENT', 'LATE', 'EXCUSED', 'ABSENT'];

export const canHaveGrade = (lessonType: string) => 
  ['lab', 'practice'].includes(lessonType.toLowerCase());
