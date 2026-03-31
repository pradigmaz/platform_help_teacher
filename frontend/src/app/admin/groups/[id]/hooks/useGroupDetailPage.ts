'use client';

import { useCallback, useEffect, useState } from 'react';
import { toast } from '@/components/ui/sonner';
import { GroupsAPI, type GroupDetailResponse } from '@/lib/api';
import { parseStudentImportNames } from '../../lib/studentImport';

export interface ActivityDialogState {
  open: boolean;
  targetId: string;
  targetName: string;
  mode: 'group' | 'student';
}

export interface StudentToDelete {
  id: string;
  name: string;
}

export interface SubgroupModalState {
  open: boolean;
  subgroup: number | null;
}

export interface AssignResult {
  matched: number;
  not_found: string[];
}

const EMPTY_ACTIVITY_DIALOG: ActivityDialogState = {
  open: false,
  targetId: '',
  targetName: '',
  mode: 'group',
};

const EMPTY_SUBGROUP_MODAL: SubgroupModalState = {
  open: false,
  subgroup: null,
};

export function useGroupDetailPage(groupId: string) {
  const [group, setGroup] = useState<GroupDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRegeneratingGroupCode, setIsRegeneratingGroupCode] = useState(false);
  const [studentToDelete, setStudentToDelete] = useState<StudentToDelete | null>(null);
  const [activityDialog, setActivityDialog] = useState<ActivityDialogState>(EMPTY_ACTIVITY_DIALOG);
  const [addStudentDialog, setAddStudentDialog] = useState(false);
  const [newStudentName, setNewStudentName] = useState('');
  const [isAddingStudent, setIsAddingStudent] = useState(false);
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [subgroupModal, setSubgroupModal] = useState<SubgroupModalState>(EMPTY_SUBGROUP_MODAL);
  const [subgroupText, setSubgroupText] = useState('');
  const [isAssigningSubgroup, setIsAssigningSubgroup] = useState(false);
  const [assignResult, setAssignResult] = useState<AssignResult | null>(null);

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

  const handleDeleteStudent = useCallback(async () => {
    if (!studentToDelete) {
      return;
    }

    try {
      await GroupsAPI.removeStudent(groupId, studentToDelete.id);
      toast.success('Студент удалён');
      await loadGroup();
    } catch {
      toast.error('Ошибка при удалении');
    } finally {
      setStudentToDelete(null);
    }
  }, [groupId, loadGroup, studentToDelete]);

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

  const handleAddStudent = useCallback(async () => {
    const name = newStudentName.trim();
    if (!name) {
      toast.error('Введите ФИО студента');
      return;
    }

    setIsAddingStudent(true);
    try {
      await GroupsAPI.addStudent(groupId, { full_name: name });
      toast.success('Студент добавлен');
      setNewStudentName('');
      setAddStudentDialog(false);
      await loadGroup();
    } catch {
      toast.error('Ошибка при добавлении студента');
    } finally {
      setIsAddingStudent(false);
    }
  }, [groupId, loadGroup, newStudentName]);

  const handlePasteSubmit = useCallback(async () => {
    const names = parseStudentImportNames(pasteText);
    if (names.length === 0) {
      toast.error('Не удалось распознать имена');
      return;
    }

    setIsImporting(true);
    try {
      const result = await GroupsAPI.addStudentsBulk(groupId, names);
      toast.success(`Добавлено студентов: ${result.added}`);
      setPasteText('');
      setShowPasteModal(false);
      await loadGroup();
    } catch {
      toast.error('Ошибка при добавлении');
    } finally {
      setIsImporting(false);
    }
  }, [groupId, loadGroup, pasteText]);

  const handleAssignSubgroup = useCallback(async () => {
    const names = parseStudentImportNames(subgroupText);
    if (names.length === 0) {
      toast.error('Не удалось распознать имена');
      return;
    }

    setIsAssigningSubgroup(true);
    try {
      const result = await GroupsAPI.assignSubgroup(groupId, subgroupModal.subgroup, names);
      setAssignResult({ matched: result.matched, not_found: result.not_found });
      if (result.not_found.length === 0) {
        toast.success(`Назначено: ${result.matched} студентов`);
        setSubgroupModal(EMPTY_SUBGROUP_MODAL);
        setSubgroupText('');
        setAssignResult(null);
      } else {
        toast.warning(`Назначено: ${result.matched}, не найдено: ${result.not_found.length}`);
      }
      await loadGroup();
    } catch {
      toast.error('Ошибка при назначении подгруппы');
    } finally {
      setIsAssigningSubgroup(false);
    }
  }, [groupId, loadGroup, subgroupModal.subgroup, subgroupText]);

  const handleClearSubgroups = useCallback(async () => {
    try {
      const result = await GroupsAPI.clearSubgroups(groupId);
      toast.success(`Подгруппы убраны у ${result.cleared} студентов`);
      await loadGroup();
    } catch {
      toast.error('Ошибка при очистке подгрупп');
    }
  }, [groupId, loadGroup]);

  const openGroupActivityDialog = useCallback(() => {
    if (!group) {
      return;
    }
    setActivityDialog({
      open: true,
      targetId: group.id,
      targetName: group.name,
      mode: 'group',
    });
  }, [group]);

  return {
    group,
    isLoading,
    loadGroup,
    isGenerating,
    isRegeneratingGroupCode,
    handleGenerateCodes,
    handleRegenerateCode,
    handleRegenerateGroupCode,
    studentToDelete,
    setStudentToDelete,
    handleDeleteStudent,
    handleDeleteStudentsBulk,
    activityDialog,
    setActivityDialog,
    openGroupActivityDialog,
    addStudentDialog,
    setAddStudentDialog,
    newStudentName,
    setNewStudentName,
    isAddingStudent,
    handleAddStudent,
    showPasteModal,
    setShowPasteModal,
    pasteText,
    setPasteText,
    isImporting,
    handlePasteSubmit,
    subgroupModal,
    setSubgroupModal,
    subgroupText,
    setSubgroupText,
    isAssigningSubgroup,
    assignResult,
    handleAssignSubgroup,
    handleClearSubgroups,
    resetPasteModal: () => {
      setShowPasteModal(false);
      setPasteText('');
    },
    resetSubgroupModal: () => {
      setSubgroupModal(EMPTY_SUBGROUP_MODAL);
      setSubgroupText('');
      setAssignResult(null);
    },
  };
}
