'use client';

import type { StudentDetailData } from '@/lib/api';
import type { ReportAttestation } from '../../../reportNavigation';

export type AttestationStatusKind = 'in_progress' | 'passing' | 'failing';

export interface AttestationSummary {
  attestationLabel: string;
  maxPoints: number;
  minPassing: number;
  totalScore: number;
  isPassing: boolean;
  isEarlySemester: boolean;
  isExcellent: boolean;
  progressPercent: number;
  groupAverage?: number;
  averageSummary: string | null;
  statusKind: AttestationStatusKind;
  statusLabel: string;
  statusMessage: string;
  gradeSummary: string;
}

export function buildAttestationSummary(
  data: StudentDetailData,
  attestationType: ReportAttestation,
): AttestationSummary {
  const maxPoints = data.max_points || 35;
  const minPassing = data.min_passing_points || 20;
  const totalScore = data.total_score || 0;
  const isPassing = data.is_passing ?? totalScore >= minPassing;
  const isEarlySemester = data.is_early_semester ?? false;
  const progressPercent = Math.min((totalScore / Math.max(maxPoints, 1)) * 100, 100);
  const differenceToPassing = Math.max(minPassing - totalScore, 0);
  const groupAverage = data.group_average_score;
  const comparisonDelta = groupAverage === undefined ? null : totalScore - groupAverage;
  const isExcellent = totalScore >= maxPoints * 0.85;

  return {
    attestationLabel: getAttestationLabel(attestationType),
    maxPoints,
    minPassing,
    totalScore,
    isPassing,
    isEarlySemester,
    isExcellent,
    progressPercent,
    groupAverage,
    averageSummary: buildAverageSummary(comparisonDelta),
    statusKind: isEarlySemester ? 'in_progress' : isPassing ? 'passing' : 'failing',
    statusLabel: isEarlySemester
      ? 'Семестр в процессе'
      : isPassing
        ? 'Зачёт получен'
        : 'Нужно добрать баллы',
    statusMessage: isEarlySemester
      ? 'Пока важнее динамика, чем итоговая оценка.'
      : isPassing
        ? 'Текущий результат уже выше порога.'
        : `До зачёта не хватает ${differenceToPassing.toFixed(1)} балла.`,
    gradeSummary: buildGradeSummary(data.grade, isPassing, isEarlySemester, isExcellent),
  };
}

export function getAttestationLabel(attestationType: ReportAttestation): string {
  return attestationType === 'second' ? '2 аттестация' : '1 аттестация';
}

function buildAverageSummary(comparisonDelta: number | null): string | null {
  if (comparisonDelta === null) {
    return null;
  }
  if (comparisonDelta > 0) {
    return `Выше среднего на +${comparisonDelta.toFixed(1)}`;
  }
  if (comparisonDelta < 0) {
    return `Ниже среднего на ${comparisonDelta.toFixed(1)}`;
  }
  return 'На уровне среднего по группе';
}

function buildGradeSummary(
  grade: string | undefined,
  isPassing: boolean,
  isEarlySemester: boolean,
  isExcellent: boolean,
): string {
  if (!grade) {
    return 'Итог пока не выставлен';
  }
  if (isEarlySemester) {
    return `Итог: ${grade}`;
  }
  if (isExcellent) {
    return `Итог: ${grade}. Сильный результат.`;
  }
  return isPassing ? `Итог: ${grade}` : `Итог: ${grade}.`;
}
