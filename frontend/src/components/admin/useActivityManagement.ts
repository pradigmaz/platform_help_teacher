'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import {
  ActivitiesAPI,
  GroupsAPI,
  type ActivityWithStudentResponse,
  type AttestationType,
  type GroupResponse,
} from '@/lib/api';
import { groupActivitiesByBatch } from './activityManagementModel';

interface StudentOption {
  id: string;
  full_name: string;
}

export function useActivityManagement(attestationType: AttestationType) {
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState('');
  const [students, setStudents] = useState<StudentOption[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [allActivities, setAllActivities] = useState<ActivityWithStudentResponse[]>([]);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [loadingActivities, setLoadingActivities] = useState(true);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [targetMode, setTargetMode] = useState<'group' | 'student'>('group');

  const loadGroups = useCallback(async () => {
    try {
      const data = await GroupsAPI.list();
      setGroups(data);
    } catch {
      toast.error('Не удалось загрузить группы');
    }
  }, []);

  const loadStudents = useCallback(async (groupId: string) => {
    setLoadingStudents(true);
    try {
      const group = await GroupsAPI.get(groupId);
      setStudents(group.students || []);
    } catch {
      toast.error('Не удалось загрузить студентов');
    } finally {
      setLoadingStudents(false);
    }
  }, []);

  const loadAllActivities = useCallback(async () => {
    setLoadingActivities(true);
    try {
      const data = await ActivitiesAPI.getAll(attestationType, 100);
      setAllActivities(data);
    } catch {
      toast.error('Не удалось загрузить активности');
    } finally {
      setLoadingActivities(false);
    }
  }, [attestationType]);

  useEffect(() => {
    void loadGroups();
    void loadAllActivities();
  }, [loadAllActivities, loadGroups]);

  useEffect(() => {
    if (selectedGroupId) {
      void loadStudents(selectedGroupId);
      return;
    }

    setStudents([]);
    setSelectedStudentId('');
  }, [loadStudents, selectedGroupId]);

  const handleDelete = useCallback(async () => {
    if (!deleteId) {
      return;
    }

    try {
      await ActivitiesAPI.delete(deleteId);
      toast.success('Активность удалена');
      await loadAllActivities();
    } catch {
      toast.error('Ошибка при удалении');
    } finally {
      setDeleteId(null);
    }
  }, [deleteId, loadAllActivities]);

  const groupedActivities = useMemo(() => groupActivitiesByBatch(allActivities), [allActivities]);
  const selectedGroup = groups.find((group) => group.id === selectedGroupId);
  const selectedStudent = students.find((student) => student.id === selectedStudentId);

  return {
    groups,
    selectedGroupId,
    setSelectedGroupId,
    students,
    selectedStudentId,
    setSelectedStudentId,
    loadingStudents,
    loadingActivities,
    addDialogOpen,
    setAddDialogOpen,
    deleteId,
    setDeleteId,
    targetMode,
    setTargetMode,
    groupedActivities,
    selectedGroup,
    selectedStudent,
    handleDelete,
    loadAllActivities,
  };
}
