import type { StudentLab } from '@/lib/api';
import { getResolvedLabStatus, isLabAccepted } from '@/lib/labs/progress';
import type { FilterStatus } from './types';

export function getLabsFilterCounts(labs: StudentLab[]) {
  const accepted = labs.filter(isLabAccepted).length;
  const inQueue = labs.filter((lab) => getResolvedLabStatus(lab) === 'pending').length;
  const rejected = labs.filter((lab) => getResolvedLabStatus(lab) === 'rejected').length;
  const notSubmitted = labs.filter((lab) => lab.is_available && getResolvedLabStatus(lab) === 'not_submitted').length;

  return { all: labs.length, accepted, in_queue: inQueue, rejected, not_submitted: notSubmitted };
}

export function getFilteredLabs(labs: StudentLab[], filter: FilterStatus) {
  if (filter === 'all') return labs;
  if (filter === 'accepted') return labs.filter(isLabAccepted);
  if (filter === 'in_queue') return labs.filter((lab) => getResolvedLabStatus(lab) === 'pending');
  if (filter === 'rejected') return labs.filter((lab) => getResolvedLabStatus(lab) === 'rejected');
  return labs.filter((lab) => lab.is_available && getResolvedLabStatus(lab) === 'not_submitted');
}
