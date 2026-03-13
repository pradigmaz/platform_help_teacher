/**
 * Константы академического календаря.
 * 
 * ВАЖНО: Эти константы используются как FALLBACK когда API недоступен.
 * Основной источник данных о семестре - эндпоинт /semester-info
 * и настройки аттестации (semester_start_date).
 * 
 * @see useSemesterInfo hook для получения актуальных данных
 */

// Недели аттестационных периодов.
// SECOND кумулятивна: период идёт от начала семестра до 14-й недели.
export const ATTESTATION_WEEKS = {
  first: 8,
  second: 14,
} as const;

/**
 * FALLBACK месяцы семестров (0-indexed: январь = 0)
 * Используются только когда semester_start_date не задан в настройках.
 */
export const SEMESTER_MONTHS = {
  fall: {
    startMonth: 8,  // сентябрь
    startDay: 1,
    endMonth: 11,   // декабрь
    endDay: 31,
  },
  spring: {
    startMonth: 0,  // январь
    startDay: 1,
    endMonth: 4,    // май
    endDay: 31,
  },
} as const;

/**
 * FALLBACK границы для определения текущего семестра.
 * Используются только когда API недоступен.
 * 
 * @deprecated Используйте useSemesterInfo() для получения актуального семестра
 */
export const SEMESTER_DETECTION = {
  fallStartMonth: 8,  // с сентября — осенний семестр
  springEndMonth: 4,  // до мая — весенний семестр
} as const;

// Максимальное количество работ на предмет
export const MAX_WORK_NUMBER = 20;

// Диапазон оценок
export const GRADE_RANGE = {
  min: 2,
  max: 5,
} as const;
