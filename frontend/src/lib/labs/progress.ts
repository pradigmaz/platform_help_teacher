import type { StudentLab, StudentLabDetail } from '@/lib/api';

type LabLike = Pick<StudentLab, 'is_accepted' | 'journal_grade' | 'acceptance_source' | 'submission'>;
type LabDetailLike = Pick<StudentLabDetail, 'is_accepted' | 'journal_grade' | 'acceptance_source' | 'submission'>;

export type StudentLabLike = LabLike | LabDetailLike;
export type ResolvedLabStatus = 'accepted' | 'pending' | 'rejected' | 'not_submitted';

export function isLabAccepted(lab: StudentLabLike): boolean {
  return Boolean(lab.is_accepted);
}

export function isLabRework(lab: StudentLabLike): boolean {
  return !isLabAccepted(lab) && lab.journal_grade === 2;
}

export function getResolvedLabGrade(lab: StudentLabLike): number | undefined {
  if (typeof lab.journal_grade === 'number') {
    return lab.journal_grade;
  }
  return lab.submission?.grade;
}

export function getResolvedLabStatus(lab: StudentLabLike): ResolvedLabStatus {
  if (isLabAccepted(lab)) {
    return 'accepted';
  }

  if (isLabRework(lab)) {
    return 'rejected';
  }

  switch (lab.submission?.status) {
    case 'IN_REVIEW':
    case 'READY':
      return 'pending';
    case 'REJECTED':
      return 'rejected';
    default:
      return 'not_submitted';
  }
}

export function getResolvedAcceptanceLabel(lab: StudentLabLike): string {
  if (!isLabAccepted(lab)) {
    return 'Не сдано';
  }

  if (lab.acceptance_source === 'journal' && lab.submission?.status !== 'ACCEPTED') {
    return 'Зачтено';
  }

  return 'Принято';
}

export function getResolvedLabStatusLabel(lab: StudentLabLike): string {
  const status = getResolvedLabStatus(lab);
  if (status === 'accepted') {
    return getResolvedAcceptanceLabel(lab);
  }
  if (status === 'pending') {
    return 'Проверка';
  }
  if (status === 'rejected') {
    return isLabRework(lab) ? 'Доработать' : 'Отклонено';
  }
  return 'Не сдано';
}
