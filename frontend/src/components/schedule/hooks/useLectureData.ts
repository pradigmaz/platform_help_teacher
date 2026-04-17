'use client';
'use no memo';

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { toast } from 'sonner';
import type { Student, GroupedLecture, AttendanceStatus, LessonStatus } from '../types';
import { isFutureLessonDate } from './lessonDateGuards';
import { setAttendanceStatusState } from './lessonSheetMutations';
import { clearSheetDraft, saveLectureSheetDraft } from './sheetDraftStorage';
import {
  getGroupedLectureKey,
  type RestoredLectureDraft,
  type ScheduleDraftContext,
} from './sheetDraftTypes';

interface GroupAttendanceState {
  students: Student[];
  attendance: Record<string, AttendanceStatus | null>;
  initialAttendance: Record<string, AttendanceStatus | null>;
  isLoading: boolean;
}

interface UseLectureDataProps {
  lecture: GroupedLecture | null;
  isOpen: boolean;
  draftContext: ScheduleDraftContext;
  restoredDraft?: RestoredLectureDraft | null;
}

interface UseLectureDataReturn {
  groupsData: Record<string, GroupAttendanceState>;
  expandedGroups: string[];
  toggleGroup: (groupId: string) => void;
  setAttendanceStatus: (groupId: string, studentId: string, status: AttendanceStatus | null) => void;
  saveLectureSheet: (status: LessonStatus) => Promise<void>;
  isLoading: boolean;
}

export function useLectureData({
  lecture,
  isOpen,
  draftContext,
  restoredDraft = null,
}: UseLectureDataProps): UseLectureDataReturn {
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

  const loadGroupData = useCallback(async (
    groupId: string,
    lessonId: string,
    restoredAttendance?: Record<string, AttendanceStatus | null>
  ) => {
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
        [groupId]: {
          students,
          attendance: restoredAttendance ? { ...restoredAttendance } : attMap,
          initialAttendance: attMap,
          isLoading: false,
        }
      }));
    } catch (err) {
      console.error('Failed to load group data:', err);
      setGroupsData(prev => ({
        ...prev,
        [groupId]: { students: [], attendance: {}, initialAttendance: {}, isLoading: false }
      }));
    }
  }, []);

  useEffect(() => {
    if (!lecture || !isOpen || !restoredDraft) {
      return;
    }

    if (restoredDraft.lectureKey !== getGroupedLectureKey(lecture)) {
      return;
    }

    void Promise.all(
      lecture.groups.map((group) =>
        loadGroupData(group.id, group.lesson_id, restoredDraft.attendanceByGroup[group.id])
      )
    );
  }, [isOpen, lecture, loadGroupData, restoredDraft]);

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

  const setAttendanceStatus = useCallback((groupId: string, studentId: string, nextStatus: AttendanceStatus | null) => {
    setGroupsData(prev => {
      const groupState = prev[groupId];
      if (!groupState) return prev;

      return {
        ...prev,
        [groupId]: {
          ...groupState,
          attendance: setAttendanceStatusState(groupState.attendance, studentId, nextStatus),
        }
      };
    });
  }, []);

  const saveLectureSheet = useCallback(async (status: LessonStatus) => {
    if (!lecture) {
      return;
    }

    saveLectureSheetDraft({
      kind: 'lecture',
      context: draftContext,
      lectureKey: getGroupedLectureKey(lecture),
      status,
      attendanceByGroup: Object.fromEntries(
        lecture.groups.map((group) => [group.id, groupsData[group.id]?.attendance || {}])
      ),
    });

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

    if (
      isFutureLessonDate(lecture.date) &&
      items.some((item) => item.attendance_updates.length > 0)
    ) {
      toast.error('Посещаемость можно отмечать только в день занятия или позже');
      throw new Error('future_attendance_blocked');
    }

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
    clearSheetDraft();
  }, [draftContext, groupsData, lecture]);

  return {
    groupsData,
    expandedGroups,
    toggleGroup,
    setAttendanceStatus,
    saveLectureSheet,
    isLoading,
  };
}
