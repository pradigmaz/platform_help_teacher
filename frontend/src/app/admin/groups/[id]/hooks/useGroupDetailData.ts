'use client';

import { useCallback, useEffect, useState } from 'react';
import { toast } from '@/components/ui/sonner';
import { GroupsAPI, type GroupDetailResponse } from '@/lib/api';
import { parseStudentImportNames } from '../../lib/studentImport';
import type { AssignResult, StudentToDelete } from './useGroupDetailState';

export function useGroupDetailData(groupId: string) {
  const [group, setGroup] = useState<GroupDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRegeneratingGroupCode, setIsRegeneratingGroupCode] = useState(false);
  const [isAddingStudent, setIsAddingStudent] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isAssigningSubgroup, setIsAssigningSubgroup] = useState(false);

  const loadGroup = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await GroupsAPI.get(groupId);
      setGroup(data);
    } catch (error) {
      console.error(error);
      toast.error('Ошибка загрузки данных группы');
    } finally {
      setIsLoading(false);
    }
  }, [groupId]);

  useEffect(() => {
    void loadGroup();
  }, [loadGroup]);

  const handleGenerateCodes = useCallback(async () => {
    setIsGenerating(true);
    try {
      const result = await GroupsAPI.generateCodes(groupId);
      toast.success(`Сгенерировано кодов: ${result.generated}`);
      await loadGroup();
    } catch {
      toast.error('Ошибка при генерации кодов');
    } finally {
      setIsGenerating(false);
    }
  }, [groupId, loadGroup]);

  const handleRegenerateCode = useCallback(
    async (userId: string) => {
      try {
        await GroupsAPI.regenerateUserCode(userId);
        toast.success('Код обновлён');
        await loadGroup();
      } catch {
        toast.error('Ошибка при регенерации кода');
      }
    },
    [loadGroup]
  );

  const handleRegenerateGroupCode = useCallback(async () => {
    setIsRegeneratingGroupCode(true);
    try {
      await GroupsAPI.regenerateGroupInviteCode(groupId);
      toast.success('Код группы обновлён');
      await loadGroup();
    } catch {
      toast.error('Ошибка при обновлении кода');
    } finally {
      setIsRegeneratingGroupCode(false);
    }
  }, [groupId, loadGroup]);

  const handleDeleteStudent = useCallback(
    async (studentToDelete: StudentToDelete | null) => {
      if (!studentToDelete) {
        return false;
      }

      try {
        await GroupsAPI.removeStudent(groupId, studentToDelete.id);
        toast.success('Студент удалён');
        await loadGroup();
        return true;
      } catch {
        toast.error('Ошибка при удалении');
        return false;
      }
    },
    [groupId, loadGroup]
  );

  const handleDeleteStudentsBulk = useCallback(
    async (ids: string[]) => {
      try {
        const result = await GroupsAPI.removeStudentsBulk(groupId, ids);
        toast.success(`Удалено студентов: ${result.deleted}`);
        await loadGroup();
      } catch {
        toast.error('Ошибка при удалении');
      }
    },
    [groupId, loadGroup]
  );

  const handleAddStudent = useCallback(
    async (name: string) => {
      const trimmedName = name.trim();
      if (!trimmedName) {
        toast.error('Введите ФИО студента');
        return false;
      }

      setIsAddingStudent(true);
      try {
        await GroupsAPI.addStudent(groupId, { full_name: trimmedName });
        toast.success('Студент добавлен');
        await loadGroup();
        return true;
      } catch {
        toast.error('Ошибка при добавлении студента');
        return false;
      } finally {
        setIsAddingStudent(false);
      }
    },
    [groupId, loadGroup]
  );

  const handlePasteSubmit = useCallback(
    async (pasteText: string) => {
      const names = parseStudentImportNames(pasteText);
      if (names.length === 0) {
        toast.error('Не удалось распознать имена');
        return false;
      }

      setIsImporting(true);
      try {
        const result = await GroupsAPI.addStudentsBulk(groupId, names);
        toast.success(`Добавлено студентов: ${result.added}`);
        await loadGroup();
        return true;
      } catch {
        toast.error('Ошибка при добавлении');
        return false;
      } finally {
        setIsImporting(false);
      }
    },
    [groupId, loadGroup]
  );

  const handleAssignSubgroup = useCallback(
    async (subgroup: number | null, subgroupText: string): Promise<AssignResult | null> => {
      const names = parseStudentImportNames(subgroupText);
      if (names.length === 0) {
        toast.error('Не удалось распознать имена');
        return null;
      }

      setIsAssigningSubgroup(true);
      try {
        const result = await GroupsAPI.assignSubgroup(groupId, subgroup, names);
        const assignResult = { matched: result.matched, not_found: result.not_found };
        if (result.not_found.length === 0) {
          toast.success(`Назначено: ${result.matched} студентов`);
        } else {
          toast.warning(`Назначено: ${result.matched}, не найдено: ${result.not_found.length}`);
        }
        await loadGroup();
        return assignResult;
      } catch {
        toast.error('Ошибка при назначении подгруппы');
        return null;
      } finally {
        setIsAssigningSubgroup(false);
      }
    },
    [groupId, loadGroup]
  );

  const handleClearSubgroups = useCallback(async () => {
    try {
      const result = await GroupsAPI.clearSubgroups(groupId);
      toast.success(`Подгруппы убраны у ${result.cleared} студентов`);
      await loadGroup();
    } catch {
      toast.error('Ошибка при очистке подгрупп');
    }
  }, [groupId, loadGroup]);

  return {
    group,
    isLoading,
    loadGroup,
    isGenerating,
    isRegeneratingGroupCode,
    isAddingStudent,
    isImporting,
    isAssigningSubgroup,
    handleGenerateCodes,
    handleRegenerateCode,
    handleRegenerateGroupCode,
    handleDeleteStudent,
    handleDeleteStudentsBulk,
    handleAddStudent,
    handlePasteSubmit,
    handleAssignSubgroup,
    handleClearSubgroups,
  };
}
