'use client';

import { useState } from 'react';

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

export const EMPTY_ACTIVITY_DIALOG: ActivityDialogState = {
  open: false,
  targetId: '',
  targetName: '',
  mode: 'group',
};

export const EMPTY_SUBGROUP_MODAL: SubgroupModalState = {
  open: false,
  subgroup: null,
};

export function useGroupDetailState() {
  const [studentToDelete, setStudentToDelete] = useState<StudentToDelete | null>(null);
  const [activityDialog, setActivityDialog] = useState<ActivityDialogState>(EMPTY_ACTIVITY_DIALOG);
  const [addStudentDialog, setAddStudentDialog] = useState(false);
  const [newStudentName, setNewStudentName] = useState('');
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [subgroupModal, setSubgroupModal] = useState<SubgroupModalState>(EMPTY_SUBGROUP_MODAL);
  const [subgroupText, setSubgroupText] = useState('');
  const [assignResult, setAssignResult] = useState<AssignResult | null>(null);

  return {
    studentToDelete,
    setStudentToDelete,
    activityDialog,
    setActivityDialog,
    addStudentDialog,
    setAddStudentDialog,
    newStudentName,
    setNewStudentName,
    showPasteModal,
    setShowPasteModal,
    pasteText,
    setPasteText,
    subgroupModal,
    setSubgroupModal,
    subgroupText,
    setSubgroupText,
    assignResult,
    setAssignResult,
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
