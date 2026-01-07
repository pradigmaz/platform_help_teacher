import { BookOpen, FlaskConical, GraduationCap } from 'lucide-react';

export const LESSON_TIMES: Record<number, { start: string; end: string }> = {
  1: { start: '08:30', end: '10:00' },
  2: { start: '10:10', end: '11:40' },
  3: { start: '11:50', end: '13:20' },
  4: { start: '13:40', end: '15:10' },
  5: { start: '15:20', end: '16:50' },
  6: { start: '17:00', end: '18:30' },
  7: { start: '18:40', end: '20:10' },
  8: { start: '20:20', end: '21:50' },
};

export const WEEKDAYS = [
  { key: 'mon', label: 'Пн', full: 'Понедельник' },
  { key: 'tue', label: 'Вт', full: 'Вторник' },
  { key: 'wed', label: 'Ср', full: 'Среда' },
  { key: 'thu', label: 'Чт', full: 'Четверг' },
  { key: 'fri', label: 'Пт', full: 'Пятница' },
  { key: 'sat', label: 'Сб', full: 'Суббота' },
];

// Базовая конфигурация (lowercase only)
const BASE_LESSON_TYPE_CONFIG = {
  lecture: {
    label: 'Лекция',
    shortLabel: 'Лек',
    icon: GraduationCap,
    bg: 'bg-blue-100 dark:bg-blue-900/50',
    border: 'border-l-blue-500',
    text: 'text-blue-800 dark:text-blue-200',
    badge: 'bg-blue-500 text-white',
    dot: 'bg-blue-500',
  },
  lab: {
    label: 'Лаб. работа',
    shortLabel: 'Лаб',
    icon: FlaskConical,
    bg: 'bg-purple-100 dark:bg-purple-900/50',
    border: 'border-l-purple-500',
    text: 'text-purple-800 dark:text-purple-200',
    badge: 'bg-purple-500 text-white',
    dot: 'bg-purple-500',
  },
  practice: {
    label: 'Практика',
    shortLabel: 'Пр',
    icon: BookOpen,
    bg: 'bg-emerald-100 dark:bg-emerald-900/50',
    border: 'border-l-emerald-500',
    text: 'text-emerald-800 dark:text-emerald-200',
    badge: 'bg-emerald-500 text-white',
    dot: 'bg-emerald-500',
  },
} as const;

export type LessonTypeKey = keyof typeof BASE_LESSON_TYPE_CONFIG;

/**
 * Получить конфигурацию типа занятия (нормализует UPPERCASE -> lowercase)
 */
export function getLessonTypeConfig(type: string) {
  const normalized = type.toLowerCase() as LessonTypeKey;
  return BASE_LESSON_TYPE_CONFIG[normalized] ?? BASE_LESSON_TYPE_CONFIG.lecture;
}

// Для обратной совместимости — экспортируем объект с обоими вариантами
export const LESSON_TYPE_CONFIG = {
  ...BASE_LESSON_TYPE_CONFIG,
  LECTURE: BASE_LESSON_TYPE_CONFIG.lecture,
  LAB: BASE_LESSON_TYPE_CONFIG.lab,
  PRACTICE: BASE_LESSON_TYPE_CONFIG.practice,
} as const;

export type LessonType = keyof typeof LESSON_TYPE_CONFIG;
