'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Users, Key, BarChart3, Plus, Sparkles, ClipboardPaste, FileText, Users2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Command, CommandInput } from '@/components/ui/command';
import { DotPattern } from '@/components/ui/dot-pattern';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion, AnimatePresence } from 'motion/react';
import { AddActivityDialog } from '@/components/admin/AddActivityDialog';
import {
  StudentsTab,
  SubgroupsTab,
  CodesTab,
  StatsTab,
  PasteStudentsModal,
  SubgroupModal,
  AddStudentDialog,
  DeleteStudentDialog,
} from './_components';
import { GroupPageSkeleton } from './_components/GroupPageSkeleton';
import { useGroupDetailPage } from './hooks/useGroupDetailPage';

type Tab = 'students' | 'subgroups' | 'codes' | 'stats';

export default function GroupDetailPage() {
  const params = useParams();
  const router = useRouter();
  const groupId = params.id as string;

  const [activeTab, setActiveTab] = useState<Tab>('students');
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
      
      {/* Header */}
      <div className="relative flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push('/admin/groups')}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{group.name}</h1>
            <p className="text-muted-foreground">{group.code} • {group.students.length} студентов</p>
          </div>
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowPasteModal(true)}>
            <ClipboardPaste className="w-4 h-4 mr-2" /> Вставить
          </Button>
          <Button variant="outline" onClick={() => setAddStudentDialog(true)} className="gap-2">
            <Plus className="w-4 h-4" /> Добавить
          </Button>
          <Button variant="outline" onClick={() => router.push(`/admin/groups/${groupId}/reports`)} className="gap-2">
            <FileText className="w-4 h-4" /> Отчёты
          </Button>
          <Button onClick={openGroupActivityDialog} className="gap-2">
            <Sparkles className="w-4 h-4" /> Активность
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as Tab)} className="mb-6">
        <TabsList className={`grid w-fit ${group.has_subgroups ? 'grid-cols-4' : 'grid-cols-3'}`}>
          <TabsTrigger value="students" className="flex items-center gap-2">
            <Users className="w-4 h-4" /> Студенты
          </TabsTrigger>
          {group.has_subgroups && (
            <TabsTrigger value="subgroups" className="flex items-center gap-2">
              <Users2 className="w-4 h-4" /> Подгруппы
            </TabsTrigger>
          )}
          <TabsTrigger value="codes" className="flex items-center gap-2">
            <Key className="w-4 h-4" /> Инвайт-коды
          </TabsTrigger>
          <TabsTrigger value="stats" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" /> Статистика
          </TabsTrigger>
        </TabsList>

        {(activeTab === 'students' || activeTab === 'codes') && (
          <div className="mt-6 mb-6">
            <Command className="border rounded-lg shadow-sm">
              <CommandInput placeholder="Поиск студентов по ФИО..." value={searchQuery} onValueChange={setSearchQuery} />
            </Command>
          </div>
        )}
      </Tabs>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'students' && (
            <StudentsTab
              students={group.students}
              searchQuery={searchQuery}
              onDeleteStudent={(id, name) => setStudentToDelete({ id, name })}
              onDeleteStudentsBulk={handleDeleteStudentsBulk}
            />
          )}
          {activeTab === 'subgroups' && group.has_subgroups && (
            <SubgroupsTab
              students={group.students}
              onAssignSubgroup={(sg) => setSubgroupModal({ open: true, subgroup: sg })}
              onClearSubgroups={handleClearSubgroups}
            />
          )}
          {activeTab === 'codes' && (
            <CodesTab
              students={group.students}
              searchQuery={searchQuery}
              groupInviteCode={group.invite_code}
              onGenerateCodes={handleGenerateCodes}
              onRegenerateCode={handleRegenerateCode}
              onRegenerateGroupCode={handleRegenerateGroupCode}
              isGenerating={isGenerating}
              isRegeneratingGroupCode={isRegeneratingGroupCode}
            />
          )}
          {activeTab === 'stats' && <StatsTab />}
        </motion.div>
      </AnimatePresence>

      {/* Dialogs & Modals */}
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
