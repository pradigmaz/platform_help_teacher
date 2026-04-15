'use client';

import type {
  AttendanceDistribution,
  AttendanceStats,
  LabProgress,
  PublicReportData,
  PublicStudentData,
} from '@/lib/api';

export type ReportSubgroupFilter = 'all' | '1' | '2';

const EMPTY_DISTRIBUTION: AttendanceDistribution = {
  present: 0,
  late: 0,
  excused: 0,
  absent: 0,
};

function toSubgroupNumber(subgroup: ReportSubgroupFilter): number | null {
  if (subgroup === 'all') {
    return null;
  }

  return Number(subgroup);
}

export function getAvailableSubgroups(data: PublicReportData): ReportSubgroupFilter[] {
  if (!data.has_subgroups) {
    return ['all'];
  }

  const subgroups = new Set<string>();

  data.students.forEach((student) => {
    if (student.subgroup === 1 || student.subgroup === 2) {
      subgroups.add(String(student.subgroup));
    }
  });

  Object.keys(data.attendance_stats?.by_subgroup ?? {}).forEach((subgroup) => {
    if (subgroup === '1' || subgroup === '2') {
      subgroups.add(subgroup);
    }
  });

  Object.keys(data.lab_progress_by_subgroup ?? {}).forEach((subgroup) => {
    if (subgroup === '1' || subgroup === '2') {
      subgroups.add(subgroup);
    }
  });

  const ordered = [...subgroups].sort() as Array<'1' | '2'>;
  return ['all', ...ordered];
}

export function filterStudentsBySubgroup(
  students: PublicStudentData[],
  subgroup: ReportSubgroupFilter,
): PublicStudentData[] {
  const subgroupNumber = toSubgroupNumber(subgroup);
  if (subgroupNumber === null) {
    return students;
  }

  return students.filter((student) => student.subgroup === subgroupNumber);
}

export function getAttendanceDistributionForSubgroup(
  distribution: AttendanceDistribution | undefined,
  stats: AttendanceStats | undefined,
  subgroup: ReportSubgroupFilter,
): AttendanceDistribution {
  if (subgroup === 'all') {
    return distribution ?? stats?.distribution ?? EMPTY_DISTRIBUTION;
  }

  return stats?.by_subgroup?.[subgroup] ?? EMPTY_DISTRIBUTION;
}

export function getAttendanceTrendForSubgroup(
  stats: AttendanceStats | undefined,
  subgroup: ReportSubgroupFilter,
): AttendanceStats['trend'] {
  if (!stats?.trend) {
    return [];
  }

  if (subgroup === 'all') {
    return stats.trend;
  }

  return stats.trend.filter((item) => item.subgroup?.toString() === subgroup);
}

export function getLabProgressForSubgroup(
  progress: LabProgress[] | undefined,
  progressBySubgroup: Record<string, LabProgress[]> | undefined,
  subgroup: ReportSubgroupFilter,
): LabProgress[] {
  if (subgroup === 'all') {
    return progress ?? [];
  }

  return progressBySubgroup?.[subgroup] ?? [];
}
