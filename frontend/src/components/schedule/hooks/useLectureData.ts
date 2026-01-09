'use client';
'use no memo';

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import type { Student, GroupedLecture, AttendanceStatus } from '../types';
import { ATTENDANCE_CYCLE } from '../constants';

interface GroupAttendanceState {
  students: Student[];
  attendance: Record<string, AttendanceStatus | null>;
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
  saveAttendance: (groupId: string, lessonId: string) => Promise<void>;
  isLoading: boolean;
}

export function useLectureData({ lecture, isOpen }: UseLectureDataProps): UseLectureDataReturn {
  const [groupsData, setGroupsData] = useState<Record<string, GroupAttendanceState>>({});
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

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
      [groupId]: { ...prev[groupId], isLoading: true, students: prev[groupId]?.students || [], attendance: prev[groupId]?.attendance || {} }
    }));

    try {
      // Load students from admin endpoint
      const { data: students } = await api.get(`/admin/schedule/groups/${groupId}/students`);

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
        [groupId]: { students, attendance: attMap, isLoading: false }
      }));
    } catch (err) {
      console.error('Failed to load group data:', err);
      setGroupsData(prev => ({
        ...prev,
        [groupId]: { students: [], attendance: {}, isLoading: false }
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

      const current = groupState.attendance[studentId];
      let next: AttendanceStatus;
      if (!current) {
        next = 'PRESENT';
      } else {
        const idx = ATTENDANCE_CYCLE.indexOf(current);
        next = ATTENDANCE_CYCLE[(idx + 1) % ATTENDANCE_CYCLE.length];
      }

      return {
        ...prev,
        [groupId]: {
          ...groupState,
          attendance: { ...groupState.attendance, [studentId]: next }
        }
      };
    });
  }, []);

  const saveAttendance = useCallback(async (groupId: string, lessonId: string) => {
    const groupState = groupsData[groupId];
    if (!groupState) return;

    const records = Object.entries(groupState.attendance)
      .filter(([_, status]) => status)
      .map(([student_id, status]) => ({ student_id, status }));

    if (records.length > 0) {
      await api.post('/admin/journal/attendance/bulk', {
        lesson_id: lessonId,
        records
      });
    }
  }, [groupsData]);

  return {
    groupsData,
    expandedGroups,
    toggleGroup,
    cycleAttendance,
    saveAttendance,
    isLoading,
  };
}
