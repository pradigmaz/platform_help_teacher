/**
 * Типы для системы аттестации (автобалансировка).
 */

export type AttestationType = 'first' | 'second';

export interface ScorePreview {
  component: string;
  weight: number;
  max_points: number;
  points_per_unit: number;
  unit_label: string;
}

export interface AttestationSettings {
  id: string;
  attestation_type: AttestationType;
  
  // Веса компонентов (сумма = 100%)
  labs_weight: number;
  attendance_weight: number;
  activity_reserve: number;
  
  // Количество работ
  labs_count_first: number;
  labs_count_second: number;
  
  // Коэффициенты оценок (5=1.0 и 2=0.0 фиксированы)
  grade_4_coef: number;
  grade_3_coef: number;
  
  // Посещаемость
  late_coef: number;
  
  // Дедлайны
  late_max_grade: number;
  very_late_max_grade: number;
  late_threshold_days: number;
  
  // Опциональные компоненты
  self_works_enabled: boolean;
  self_works_weight: number;
  self_works_count: number;
  colloquium_enabled: boolean;
  colloquium_weight: number;
  colloquium_count: number;
  
  // Активность
  activity_enabled: boolean;
  
  // Периоды
  period_start_date: string | null;
  period_end_date: string | null;
  semester_start_date: string | null;
  
  // Мета
  created_at: string;
  updated_at: string;
  max_points: number;
  min_passing_points: number;
  grade_scale: Record<string, [number, number]>;
  score_preview: ScorePreview[];
  calculated_period_start: string | null;
  calculated_period_end: string | null;
}

export interface AttestationSettingsUpdate {
  attestation_type: AttestationType;
  labs_weight: number;
  attendance_weight: number;
  activity_reserve: number;
  labs_count_first: number;
  labs_count_second: number;
  grade_4_coef: number;
  grade_3_coef: number;
  late_coef: number;
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
  period_start_date?: string | null;
  period_end_date?: string | null;
  semester_start_date?: string | null;
}

export interface ComponentBreakdown {
  labs_score: number;
  labs_count: number;
  labs_max: number;
  attendance_score: number;
  attendance_ratio: number;
  attendance_max: number;
  total_classes: number;
  present_count: number;
  late_count: number;
  excused_count: number;
  absent_count: number;
  activity_score: number;
  activity_max: number;
  bonus_blocked: boolean;
  self_works_score?: number;
  colloquium_score?: number;
}

export interface AttestationResult {
  student_id: string;
  student_name: string;
  attestation_type: AttestationType;
  group_code?: string;
  total_score: number;
  grade: string;
  is_passing: boolean;
  max_points: number;
  min_passing_points: number;
  breakdown: ComponentBreakdown;
  calculated_at?: string;
}

export interface GroupAttestationResult {
  group_id: string;
  group_code: string;
  attestation_type: AttestationType;
  calculated_at: string;
  total_students: number;
  passing_students: number;
  failing_students: number;
  grade_distribution: Record<string, number>;
  average_score: number;
  students: AttestationResult[];
}

export interface GradeScale {
  max: number;
  min: number;
  grades: {
    excellent: [number, number];
    good: [number, number];
    satisfactory: [number, number];
    unsatisfactory: [number, number];
  };
}

export type BackendGradeScale = Record<string, [number, number]>;

const GRADE_KEY_MAP: Record<string, keyof GradeScale['grades']> = {
  'отл': 'excellent',
  'хор': 'good',
  'уд': 'satisfactory',
  'неуд': 'unsatisfactory',
};

export function convertGradeScale(
  backendScale: BackendGradeScale,
  attestationType: AttestationType
): GradeScale {
  const maxPoints = attestationType === 'first' ? 35 : 70;
  const minPoints = attestationType === 'first' ? 20 : 40;
  
  const grades: GradeScale['grades'] = {
    excellent: [0, 0],
    good: [0, 0],
    satisfactory: [0, 0],
    unsatisfactory: [0, 0],
  };
  
  for (const [ruKey, range] of Object.entries(backendScale)) {
    const enKey = GRADE_KEY_MAP[ruKey];
    if (enKey) {
      grades[enKey] = range;
    }
  }
  
  return { max: maxPoints, min: minPoints, grades };
}
