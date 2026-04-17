const MSK_DATE_FORMATTER = new Intl.DateTimeFormat('sv-SE', {
  timeZone: 'Europe/Moscow',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

export function getMskDate(now: Date = new Date()) {
  return MSK_DATE_FORMATTER.format(now);
}

export function isFutureLessonDate(lessonDate: string, today = getMskDate()) {
  return lessonDate > today;
}
