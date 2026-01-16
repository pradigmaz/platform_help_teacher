/**
 * Склонение слова "студент" в зависимости от числа
 * @param count - количество студентов
 * @returns правильная форма слова
 * 
 * @example
 * pluralizeStudents(1) // "1 студент"
 * pluralizeStudents(2) // "2 студента"
 * pluralizeStudents(5) // "5 студентов"
 * pluralizeStudents(21) // "21 студент"
 */
export function pluralizeStudents(count: number): string {
  const lastDigit = count % 10;
  const lastTwoDigits = count % 100;

  if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
    return `${count} студентов`;
  }

  if (lastDigit === 1) {
    return `${count} студент`;
  }

  if (lastDigit >= 2 && lastDigit <= 4) {
    return `${count} студента`;
  }

  return `${count} студентов`;
}

/**
 * Только форма слова без числа
 */
export function getStudentWord(count: number): string {
  const lastDigit = count % 10;
  const lastTwoDigits = count % 100;

  if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
    return 'студентов';
  }

  if (lastDigit === 1) {
    return 'студент';
  }

  if (lastDigit >= 2 && lastDigit <= 4) {
    return 'студента';
  }

  return 'студентов';
}
