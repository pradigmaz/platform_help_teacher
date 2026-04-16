export interface AttestationFormState {
  labs_weight: number;
  attendance_weight: number;
  activity_reserve: number;
  labs_count_first: number;
  labs_count_second: number;
  grade_4_coef: number;
  grade_3_coef: number;
  late_coef: number;
  absent_coef: number;
  late_max_grade: number;
  very_late_max_grade: number;
  late_threshold_days: number;
  self_works_enabled: boolean;
  self_works_weight: number;
  self_works_count: number;
  colloquium_enabled: boolean;
  colloquium_weight: number;
  colloquium_count: number;
  activity_enabled: boolean;
  expected_lessons_per_week: number;
  semester_start_date: string;
}

export const DEFAULT_FORM_STATE: AttestationFormState = {
  labs_weight: 70,
  attendance_weight: 30,
  activity_reserve: 10,
  labs_count_first: 8,
  labs_count_second: 10,
  grade_4_coef: 0.7,
  grade_3_coef: 0.4,
  late_coef: 0.5,
  absent_coef: 0,
  late_max_grade: 4,
  very_late_max_grade: 3,
  late_threshold_days: 7,
  self_works_enabled: false,
  self_works_weight: 0,
  self_works_count: 2,
  colloquium_enabled: false,
  colloquium_weight: 0,
  colloquium_count: 1,
  activity_enabled: true,
  expected_lessons_per_week: 2,
  semester_start_date: '',
};

export function formatPeriod(startDate: string, weekStart: number, weekEnd: number): string {
  const start = new Date(startDate);
  const periodStart = new Date(start);
  periodStart.setDate(start.getDate() + (weekStart - 1) * 7);
  const periodEnd = new Date(start);
  periodEnd.setDate(start.getDate() + weekEnd * 7 - 1);
  
  const formatDate = (d: Date) => d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
  return `${formatDate(periodStart)} — ${formatDate(periodEnd)}`;
}
