'use client';
'use no memo';

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import type { Student, GroupedLecture, AttendanceStatus, LessonStatus } from '../types';
import { ATTENDANCE_CYCLE } from '../constants';

interface GroupAttendanceState {
  students: Student[];
  attendance: Record<string, AttendanceStatus | null>;
  initialAttendance: Record<string, AttendanceStatus | null>;
  isLoading: boolean;
}

interface UseLectureDataProps {
  lecture: GroupedLecture | null;
  isOpen: boolean;
}

interface UseLectureDataReturn {
  groupsData: Record<string, GroupAttendanceState>;
  expandedGroups: string[];
  toggleGroup: (groupId: string) => void;
  cycleAttendance: (groupId: string, studentId: string) => void;
  saveLectureSheet: (status: LessonStatus) => Promise<void>;
  isLoading: boolean;
}

export function useLectureData({ lecture, isOpen }: UseLectureDataProps): UseLectureDataReturn {
  const [groupsData, setGroupsData] = useState<Record<string, GroupAttendanceState>>({});
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);
  const isLoading = Object.values(groupsData).some((groupState) => groupState.isLoading);

  // Reset when lecture changes
  useEffect(() => {
    if (!isOpen) {
      setGroupsData({});
      setExpandedGroups([]);
    }
  }, [isOpen, lecture?.date, lecture?.lesson_number]);

  const loadGroupData = useCallback(async (groupId: string, lessonId: string) => {
    setGroupsData(prev => ({
      ...prev,
      [groupId]: {
        ...prev[groupId],
        isLoading: true,
        students: prev[groupId]?.students || [],
        attendance: prev[groupId]?.attendance || {},
        initialAttendance: prev[groupId]?.initialAttendance || {},
      }
    }));

    try {
      // Load students from admin endpoint
      const { data: students } = await api.get(`/admin/groups/${groupId}/students`);

      // Load attendance
      const { data: attData } = await api.get('/admin/journal/attendance', {
        params: { group_id: groupId, lesson_ids: [lessonId] }
      });
      const attMap: Record<string, AttendanceStatus | null> = {};
      for (const a of attData) {
        attMap[a.student_id] = a.status as AttendanceStatus;
      }

      setGroupsData(prev => ({
        ...prev,
        [groupId]: { students, attendance: attMap, initialAttendance: attMap, isLoading: false }
      }));
    } catch (err) {
      console.error('Failed to load group data:', err);
      setGroupsData(prev => ({
        ...prev,
        [groupId]: { students: [], attendance: {}, initialAttendance: {}, isLoading: false }
      }));
    }
  }, []);

  const toggleGroup = useCallback((groupId: string) => {
    setExpandedGroups(prev => {
      const isExpanded = prev.includes(groupId);
      if (isExpanded) {
        return prev.filter(id => id !== groupId);
      } else {
        // Load data if not loaded
        if (!groupsData[groupId]?.students.length) {
          const group = lecture?.groups.find(g => g.id === groupId);
          if (group) {
            loadGroupData(groupId, group.lesson_id);
          }
        }
        return [...prev, groupId];
      }
    });
  }, [groupsData, lecture, loadGroupData]);

  const cycleAttendance = useCallback((groupId: string, studentId: string) => {
    setGroupsData(prev => {
      const groupState = prev[groupId];
      if (!groupState) return prev;

      const current = groupState.attendance[studentId] ?? null;
      if (!current) {
        return {
          ...prev,
          [groupId]: {
            ...groupState,
            attendance: { ...groupState.attendance, [studentId]: 'PRESENT' },
          }
        };
      }

      if (current === ATTENDANCE_CYCLE[ATTENDANCE_CYCLE.length - 1]) {
        const nextAttendance = { ...groupState.attendance };
        delete nextAttendance[studentId];
        return {
          ...prev,
          [groupId]: {
            ...groupState,
            attendance: nextAttendance,
          }
        };
      }

      const idx = ATTENDANCE_CYCLE.indexOf(current);
      const next = idx >= 0 ? ATTENDANCE_CYCLE[idx + 1] : ATTENDANCE_CYCLE[0];

      return {
        ...prev,
        [groupId]: {
          ...groupState,
          attendance: { ...groupState.attendance, [studentId]: next }
        }
      };
    });
  }, []);

  const saveLectureSheet = useCallback(async (status: LessonStatus) => {
    if (!lecture) {
      return;
    }

    const items = lecture.groups.map((group) => {
      const groupState = groupsData[group.id];
      const currentAttendance = groupState?.attendance || {};
      const initialAttendance = groupState?.initialAttendance || {};
      const studentIds = new Set([
        ...Object.keys(initialAttendance),
        ...Object.keys(currentAttendance),
      ]);

      return {
        lesson_id: group.lesson_id,
        attendance_updates: Array.from(studentIds)
          .map((studentId) => ({
            student_id: studentId,
            status: currentAttendance[studentId] ?? null,
          }))
          .filter(
            ({ student_id, status }) => (initialAttendance[student_id] ?? null) !== status
          ),
      };
    });

    const { data } = await api.post('/admin/lectures/grouped/sheet', {
      status,
      items,
    });

    if (!Array.isArray(data?.items)) {
      return;
    }

    const groupIdByLessonId = Object.fromEntries(
      lecture.groups.map((group) => [group.lesson_id, group.id])
    ) as Record<string, string>;

    setGroupsData((prev) => {
      const next = { ...prev };
      for (const item of data.items as Array<{
        lesson_id: string;
        attendance: Array<{ student_id: string; status: AttendanceStatus | null }>;
      }>) {
        const groupId = groupIdByLessonId[item.lesson_id];
        const groupState = groupId ? next[groupId] : undefined;
        if (!groupId || !groupState) {
          continue;
        }

        const nextAttendance = Object.fromEntries(
          item.attendance
            .filter((record) => Boolean(record.status))
            .map((record) => [record.student_id, record.status])
        ) as Record<string, AttendanceStatus | null>;

        next[groupId] = {
          ...groupState,
          attendance: nextAttendance,
          initialAttendance: { ...nextAttendance },
        };
      }
      return next;
    });
  }, [groupsData, lecture]);

  return {
    groupsData,
    expandedGroups,
    toggleGroup,
    cycleAttendance,
    saveLectureSheet,
    isLoading,
  };
}
