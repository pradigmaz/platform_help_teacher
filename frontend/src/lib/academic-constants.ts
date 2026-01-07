/**
 * Константы академического календаря.
 * Централизованное место для всех дат и периодов.
 */

// Недели аттестационных периодов
export const ATTESTATION_WEEKS = {
  first: 7,   // 1-я аттестация: недели 1-7
  second: 13, // 2-я аттестация: недели 8-13
} as const;

// Месяцы семестров (0-indexed: январь = 0)
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

// Границы для определения текущего семестра
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
