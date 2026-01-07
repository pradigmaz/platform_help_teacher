export type AttestationType = 'first' | 'second';

export interface AttestationSettings {
  id: string;
  attestation_type: AttestationType;
  labs_weight: number;
  attendance_weight: number;
  activity_weight: number;
  required_labs_count: number;
  bonus_per_extra_lab: number;
  soft_deadline_penalty: number;
  hard_deadline_penalty: number;
  soft_deadline_days: number;
  present_points: number;
  late_points: number;
  excused_points: number;
  absent_points: number;
  activity_enabled: boolean;
  participation_points: number;
  period_start_date: string | null;
  period_end_date: string | null;
  created_at: string;
  updated_at: string;
  max_points: number;
  min_passing_points: number;
}

export interface AttestationSettingsUpdate {
  attestation_type: AttestationType;
  labs_weight: number;
  attendance_weight: number;
  activity_weight: number;
  required_labs_count: number;
  bonus_per_extra_lab: number;
  soft_deadline_penalty: number;
  hard_deadline_penalty: number;
  soft_deadline_days: number;
  present_points: number;
  late_points: number;
  excused_points: number;
  absent_points: number;
  activity_enabled: boolean;
  participation_points: number;
  period_start_date?: string | null;
  period_end_date?: string | null;
}

export interface ComponentBreakdown {
  labs_raw_score: number;
  labs_weighted_score: number;
  labs_count: number;
  labs_required: number;
  labs_bonus: number;
  attendance_raw_score: number;
  attendance_weighted_score: number;
  attendance_total_classes: number;
  attendance_present: number;
  attendance_late: number;
  attendance_excused: number;
  attendance_absent: number;
  activity_raw_score: number;
  activity_weighted_score: number;
}

export interface AttestationResult {
  student_id: string;
  student_name: string;
  attestation_type: AttestationType;
  total_score: number;
  lab_score: number;
  attendance_score: number;
  activity_score: number;
  grade: string;
  is_passing: boolean;
  max_points: number;
  min_passing_points: number;
  components_breakdown: ComponentBreakdown;
  calculated_at?: string;
  group_code?: string;
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

// Тип ответа от backend (русские ключи)
export type BackendGradeScale = Record<string, [number, number]>;

// Маппинг русских ключей в английские
const GRADE_KEY_MAP: Record<string, keyof GradeScale['grades']> = {
  'отл': 'excellent',
  'хор': 'good',
  'уд': 'satisfactory',
  'неуд': 'unsatisfactory',
};

/**
 * Конвертация GradeScale из backend формата в frontend формат.
 */
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

export interface ComponentsConfigAPI {
  labs: {
    enabled: boolean;
    weight: number;
    grading_mode: 'binary' | 'graded';
    grading_scale: 5 | 10 | 100;
    required_count: number;
    bonus_per_extra: number;
    soft_deadline_days: number;
    soft_deadline_penalty: number;
    hard_deadline_penalty: number;
  };
  tests: {
    enabled: boolean;
    weight: number;
    grading_scale: 5 | 10 | 100;
    required_count: number;
    allow_retakes: boolean;
    max_retakes: number;
    retake_penalty: number;
    best_n_count: number | null;
  };
  attendance: {
    enabled: boolean;
    weight: number;
    mode: 'per_class' | 'percentage';
    points_per_class: number;
    max_points: number;
    penalty_enabled: boolean;
    penalty_per_absence: number;
    excused_absence_counts: boolean;
  };
  activity: {
    enabled: boolean;
    weight: number;
    max_points: number;
    points_per_activity: number;
    allow_negative: boolean;
    negative_limit: number;
    categories_enabled: boolean;
  };
}
