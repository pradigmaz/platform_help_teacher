export interface LabSubmission {
  lab_id: string;
  lab_title: string;
  status: string | null;
  normalized_status?: string | null;
  grade: number | null;
  max_grade: number;
  deadline_5_lessons: number | null;
  deadline_4_lessons: number | null;
  submitted_at: string | null;
  feedback: string | null;
  is_overdue: boolean;
}

export interface StudentStats {
  labs_total: number;
  labs_submitted: number;
  labs_accepted: number;
  labs_rejected: number;
  labs_pending: number;
  labs_overdue: number;
  points_earned: number;
  points_max: number;
  points_percent: number;
  group_rank: number | null;
  group_total: number | null;
  group_percentile: number | null;
}

export interface StudentProfile {
  id: string;
  full_name: string;
  username: string | null;
  telegram_id: string | null;
  vk_id: string | null;
  group_name: string | null;
  group_id: string | null;
  is_active: boolean;
  created_at: string;
  labs: LabSubmission[];
  stats: StudentStats;
}

export const STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode; label: string }> = {};

export const COLORS = {
  accepted: '#22c55e',
  pending: '#eab308',
  rejected: '#ef4444',
  notSubmitted: '#94a3b8',
  overdue: '#f97316',
};
