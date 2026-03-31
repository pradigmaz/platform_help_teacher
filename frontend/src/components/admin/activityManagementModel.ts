import type { ActivityWithStudentResponse } from '@/lib/api';

export interface GroupedActivityEntry {
  key: string;
  activities: ActivityWithStudentResponse[];
  isGroup: boolean;
  first: ActivityWithStudentResponse;
  uniqueGroups: string[];
}

export function groupActivitiesByBatch(
  activities: ActivityWithStudentResponse[]
): GroupedActivityEntry[] {
  const grouped = activities.reduce<Map<string, ActivityWithStudentResponse[]>>((accumulator, activity) => {
    const key = activity.batch_id || activity.id;
    if (!accumulator.has(key)) {
      accumulator.set(key, []);
    }
    accumulator.get(key)?.push(activity);
    return accumulator;
  }, new Map());

  return Array.from(grouped.entries()).map(([key, groupedActivities]) => ({
    key,
    activities: groupedActivities,
    isGroup: groupedActivities.length > 1,
    first: groupedActivities[0],
    uniqueGroups: [
      ...new Set(
        groupedActivities
          .map((activity) => activity.group_name)
          .filter((groupName): groupName is string => Boolean(groupName))
      ),
    ],
  }));
}

export function getActivityInitials(name: string): string {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}
