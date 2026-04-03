'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { DotPattern } from '@/components/ui/dot-pattern';
import { AddActivityDialog } from '@/components/admin/AddActivityDialog';
import {
  GroupDetailHeader,
  GroupDetailTabs,
  type GroupDetailTab,
  PasteStudentsModal,
  SubgroupModal,
  AddStudentDialog,
  DeleteStudentDialog,
} from './_components';
import { GroupPageSkeleton } from './_components/GroupPageSkeleton';
import { useGroupDetailPage } from './hooks/useGroupDetailPage';

export default function GroupDetailPage() {
  const params = useParams();
  const router = useRouter();
  const groupId = params.id as string;

  const [activeTab, setActiveTab] = useState<GroupDetailTab>('students');
  const [searchQuery, setSearchQuery] = useState('');
  const {
    group,
    isLoading,
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
    resetPasteModal,
    resetSubgroupModal,
  } = useGroupDetailPage(groupId);

  if (isLoading) return <GroupPageSkeleton />;

  if (!group) {
    return (
      <div className="p-8 text-center">
        <p className="text-muted-foreground">Группа не найдена</p>
        <Button variant="outline" className="mt-4" onClick={() => router.back()}>Назад</Button>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen max-w-6xl mx-auto p-8 overflow-hidden">
      <DotPattern className="[mask-image:radial-gradient(800px_circle_at_center,white,transparent)] opacity-40" />

      <GroupDetailHeader
        group={group}
        groupId={groupId}
        onBack={() => router.push('/admin/groups')}
        onOpenPasteModal={() => setShowPasteModal(true)}
        onOpenAddStudentDialog={() => setAddStudentDialog(true)}
        onOpenReports={(nextGroupId) => router.push(`/admin/groups/${nextGroupId}/reports`)}
        onOpenActivityDialog={openGroupActivityDialog}
      />

      <GroupDetailTabs
        group={group}
        activeTab={activeTab}
        searchQuery={searchQuery}
        isGenerating={isGenerating}
        isRegeneratingGroupCode={isRegeneratingGroupCode}
        onTabChange={setActiveTab}
        onSearchQueryChange={setSearchQuery}
        onDeleteStudent={(id, name) => setStudentToDelete({ id, name })}
        onDeleteStudentsBulk={handleDeleteStudentsBulk}
        onAssignSubgroup={(subgroup) => setSubgroupModal({ open: true, subgroup })}
        onClearSubgroups={handleClearSubgroups}
        onGenerateCodes={handleGenerateCodes}
        onRegenerateCode={handleRegenerateCode}
        onRegenerateGroupCode={handleRegenerateGroupCode}
      />

      <DeleteStudentDialog
        student={studentToDelete}
        onOpenChange={() => setStudentToDelete(null)}
        onConfirm={handleDeleteStudent}
      />

      <AddActivityDialog
        open={activityDialog.open}
        onOpenChange={(open) => setActivityDialog(prev => ({ ...prev, open }))}
        targetId={activityDialog.targetId}
        targetName={activityDialog.targetName}
        mode={activityDialog.mode}
        onSuccess={() => {}}
      />

      <AddStudentDialog
        open={addStudentDialog}
        name={newStudentName}
        isAdding={isAddingStudent}
        onOpenChange={setAddStudentDialog}
        onNameChange={setNewStudentName}
        onSubmit={handleAddStudent}
      />

      <PasteStudentsModal
        open={showPasteModal}
        text={pasteText}
        isImporting={isImporting}
        onTextChange={setPasteText}
        onSubmit={handlePasteSubmit}
        onClose={resetPasteModal}
      />

      <SubgroupModal
        open={subgroupModal.open}
        subgroup={subgroupModal.subgroup}
        text={subgroupText}
        isAssigning={isAssigningSubgroup}
        assignResult={assignResult}
        onTextChange={setSubgroupText}
        onSubmit={handleAssignSubgroup}
        onClose={resetSubgroupModal}
      />
    </div>
  );
}
