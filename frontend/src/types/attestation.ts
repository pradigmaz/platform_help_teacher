// Типы конфигурации компонентов аттестации

export interface ComponentConfigBase {
  enabled: boolean;
  weight: number;
}

export interface LabsComponentConfig extends ComponentConfigBase {
  grading_mode: 'binary' | 'graded';
  grading_scale: 5 | 10 | 100;
  required_count: number;
  bonus_per_extra: number;
  soft_deadline_days: number;
  soft_deadline_penalty: number;
  hard_deadline_penalty: number;
}

export interface TestsComponentConfig extends ComponentConfigBase {
  grading_scale: 5 | 10 | 100;
  required_count: number;
  allow_retakes: boolean;
  max_retakes: number;
  retake_penalty: number;
  best_n_count: number | null;
}

export interface AttendanceComponentConfig extends ComponentConfigBase {
  mode: 'per_class' | 'percentage';
  points_per_class: number;
  max_points: number;
  penalty_enabled: boolean;
  penalty_per_absence: number;
  excused_absence_counts: boolean;
}

export interface ActivityComponentConfig extends ComponentConfigBase {
  max_points: number;
  points_per_activity: number;
  allow_negative: boolean;
  negative_limit: number;
  categories_enabled: boolean;
}

export interface ComponentsConfig {
  labs: LabsComponentConfig;
  tests: TestsComponentConfig;
  attendance: AttendanceComponentConfig;
  activity: ActivityComponentConfig;
}

export const DEFAULT_COMPONENTS_CONFIG: ComponentsConfig = {
  labs: {
    enabled: true,
    weight: 60,
    grading_mode: 'graded',
    grading_scale: 5,
    required_count: 5,
    bonus_per_extra: 0.4,
    soft_deadline_days: 7,
    soft_deadline_penalty: 0.7,
    hard_deadline_penalty: 0.5,
  },
  tests: {
    enabled: false,
    weight: 0,
    grading_scale: 5,
    required_count: 0,
    allow_retakes: true,
    max_retakes: 2,
    retake_penalty: 0.1,
    best_n_count: null,
  },
  attendance: {
    enabled: true,
    weight: 20,
    mode: 'per_class',
    points_per_class: 1,
    max_points: 20,
    penalty_enabled: true,
    penalty_per_absence: 0.5,
    excused_absence_counts: false,
  },
  activity: {
    enabled: true,
    weight: 20,
    max_points: 10,
    points_per_activity: 1,
    allow_negative: true,
    negative_limit: 5,
    categories_enabled: false,
  },
};
