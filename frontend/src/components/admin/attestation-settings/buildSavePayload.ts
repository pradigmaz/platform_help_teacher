import type { AttestationType, AttestationSettingsUpdate } from '@/lib/api';
import type { AttestationFormState } from './types';

export function buildGlobalAttestationSettingsPayload(
  attestationType: AttestationType,
  form: AttestationFormState,
): AttestationSettingsUpdate {
  return {
    attestation_type: attestationType,
    labs_weight: form.labs_weight,
    attendance_weight: form.attendance_weight,
    activity_reserve: form.activity_reserve,
    grade_4_coef: form.grade_4_coef,
    grade_3_coef: form.grade_3_coef,
    late_coef: form.late_coef,
    absent_coef: form.absent_coef,
    self_works_enabled: form.self_works_enabled,
    self_works_weight: form.self_works_weight,
    self_works_count: form.self_works_count,
    colloquium_enabled: form.colloquium_enabled,
    colloquium_weight: form.colloquium_weight,
    colloquium_count: form.colloquium_count,
    activity_enabled: form.activity_enabled,
    expected_lessons_per_week: form.expected_lessons_per_week,
    semester_start_date: form.semester_start_date || null,
  };
}

