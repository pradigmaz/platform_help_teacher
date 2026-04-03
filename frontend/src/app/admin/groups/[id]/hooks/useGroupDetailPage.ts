'use client';

import { useCallback } from 'react';
import { useGroupDetailState } from './useGroupDetailState';
import { useGroupDetailData } from './useGroupDetailData';

export function useGroupDetailPage(groupId: string) {
  const state = useGroupDetailState();
  const data = useGroupDetailData(groupId);
  const {
    newStudentName,
    pasteText,
    studentToDelete,
    subgroupModal,
    subgroupText,
  } = state;

  const handleDeleteStudent = useCallback(async () => {
    const deleted = await data.handleDeleteStudent(studentToDelete);
    if (deleted) {
      state.setStudentToDelete(null);
    }
  }, [data, state, studentToDelete]);

  const handleAddStudent = useCallback(async () => {
    const added = await data.handleAddStudent(newStudentName);
    if (added) {
      state.setNewStudentName('');
      state.setAddStudentDialog(false);
    }
  }, [data, newStudentName, state]);

  const handlePasteSubmit = useCallback(async () => {
    const imported = await data.handlePasteSubmit(pasteText);
    if (imported) {
      state.resetPasteModal();
    }
  }, [data, pasteText, state]);

  const handleAssignSubgroup = useCallback(async () => {
    const result = await data.handleAssignSubgroup(subgroupModal.subgroup, subgroupText);
    if (!result) {
      return;
    }
    if (result.not_found.length === 0) {
      state.resetSubgroupModal();
      return;
    }
    state.setAssignResult(result);
  }, [data, state, subgroupModal.subgroup, subgroupText]);

  const openGroupActivityDialog = useCallback(() => {
    if (!data.group) {
      return;
    }
    state.setActivityDialog({
      open: true,
      targetId: data.group.id,
      targetName: data.group.name,
      mode: 'group',
    });
  }, [data.group, state]);

  return {
    group: data.group,
    isLoading: data.isLoading,
    loadGroup: data.loadGroup,
    isGenerating: data.isGenerating,
    isRegeneratingGroupCode: data.isRegeneratingGroupCode,
    handleGenerateCodes: data.handleGenerateCodes,
    handleRegenerateCode: data.handleRegenerateCode,
    handleRegenerateGroupCode: data.handleRegenerateGroupCode,
    studentToDelete: state.studentToDelete,
    setStudentToDelete: state.setStudentToDelete,
    handleDeleteStudent,
    handleDeleteStudentsBulk: data.handleDeleteStudentsBulk,
    activityDialog: state.activityDialog,
    setActivityDialog: state.setActivityDialog,
    openGroupActivityDialog,
    addStudentDialog: state.addStudentDialog,
    setAddStudentDialog: state.setAddStudentDialog,
    newStudentName: state.newStudentName,
    setNewStudentName: state.setNewStudentName,
    isAddingStudent: data.isAddingStudent,
    handleAddStudent,
    showPasteModal: state.showPasteModal,
    setShowPasteModal: state.setShowPasteModal,
    pasteText: state.pasteText,
    setPasteText: state.setPasteText,
    isImporting: data.isImporting,
    handlePasteSubmit,
    subgroupModal: state.subgroupModal,
    setSubgroupModal: state.setSubgroupModal,
    subgroupText: state.subgroupText,
    setSubgroupText: state.setSubgroupText,
    isAssigningSubgroup: data.isAssigningSubgroup,
    assignResult: state.assignResult,
    handleAssignSubgroup,
    handleClearSubgroups: data.handleClearSubgroups,
    resetPasteModal: state.resetPasteModal,
    resetSubgroupModal: state.resetSubgroupModal,
  };
}
