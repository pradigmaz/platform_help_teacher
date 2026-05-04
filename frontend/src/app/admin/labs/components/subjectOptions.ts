import type { GroupSubjectOffering } from '@/lib/api';

export interface AdminLabOfferingOption {
  id: string;
  subjectId: string;
  subjectName: string;
  groupName: string;
  semester: string;
  label: string;
}

export function getAdminLabOfferingOptions(offerings: GroupSubjectOffering[]): AdminLabOfferingOption[] {
  return offerings
    .map((offering) => ({
      id: offering.id,
      subjectId: offering.subject_id,
      subjectName: offering.subject_name,
      groupName: offering.group_name,
      semester: offering.semester,
      label: `${offering.group_name} / ${offering.subject_name} / ${offering.semester}`,
    }))
    .sort((left, right) => left.label.localeCompare(right.label, 'ru'));
}

export function getSelectedOfferingOption(
  offerings: AdminLabOfferingOption[],
  offeringId: string | null,
): AdminLabOfferingOption | null {
  if (!offeringId) return null;
  return offerings.find((offering) => offering.id === offeringId) ?? null;
}
