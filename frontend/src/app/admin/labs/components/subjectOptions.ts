import type { GroupSubjectOffering } from '@/lib/api';

export interface AdminLabOfferingOption {
  id: string;
  subjectId: string;
  label: string;
}

export interface AdminLabSubjectOption {
  id: string;
  name: string;
  offeringIds: string[];
  offerings: AdminLabOfferingOption[];
}

export function getAdminLabSubjectOptions(offerings: GroupSubjectOffering[]): AdminLabSubjectOption[] {
  const bySubject = new Map<string, AdminLabSubjectOption>();

  for (const offering of offerings) {
    const existing = bySubject.get(offering.subject_id);
    const offeringOption = {
      id: offering.id,
      subjectId: offering.subject_id,
      label: `${offering.group_name} / ${offering.semester}`,
    };
    if (existing) {
      existing.offeringIds.push(offering.id);
      existing.offerings.push(offeringOption);
      continue;
    }
    bySubject.set(offering.subject_id, {
      id: offering.subject_id,
      name: offering.subject_name,
      offeringIds: [offering.id],
      offerings: [offeringOption],
    });
  }

  return Array.from(bySubject.values())
    .map((subject) => ({
      ...subject,
      offerings: subject.offerings.sort((left, right) => left.label.localeCompare(right.label, 'ru')),
    }))
    .sort((left, right) => left.name.localeCompare(right.name, 'ru'));
}

export function getSelectedSubjectOption(
  subjects: AdminLabSubjectOption[],
  subjectId: string | null,
): AdminLabSubjectOption | null {
  if (!subjectId) return null;
  return subjects.find((subject) => subject.id === subjectId) ?? null;
}
