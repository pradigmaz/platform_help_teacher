'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Sparkles } from 'lucide-react';
import { type AttestationType } from '@/lib/api';
import { AddActivityDialog } from './AddActivityDialog';
import { BlurFade } from '@/components/ui/blur-fade';
import { ActivityHistoryList } from './ActivityHistoryList';
import { ActivityTargetSelectors } from './ActivityTargetSelectors';
import { DeleteActivityDialog } from './DeleteActivityDialog';
import { useActivityManagement } from './useActivityManagement';

interface ActivityManagementSectionProps {
  attestationType: AttestationType;
}

export function ActivityManagementSection({ attestationType }: ActivityManagementSectionProps) {
  const {
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
  } = useActivityManagement(attestationType);

  return (
    <Card className="overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-purple-500/5 to-transparent">
        <CardTitle className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-purple-500/10">
            <Sparkles className="w-5 h-5 text-purple-500" />
          </div>
          Управление активностями
        </CardTitle>
        <CardDescription>
          Добавляйте бонусы или штрафы для групп или отдельных студентов
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 pt-6">
        <ActivityTargetSelectors
          groups={groups}
          selectedGroupId={selectedGroupId}
          selectedStudentId={selectedStudentId}
          students={students}
          loadingStudents={loadingStudents}
          onGroupChange={setSelectedGroupId}
          onStudentChange={(value) => setSelectedStudentId(value === '__all__' ? '' : value)}
          onOpenAddDialog={() => {
            setTargetMode(selectedStudentId ? 'student' : 'group');
            setAddDialogOpen(true);
          }}
        />

        <div className="border-t my-4" />
        <BlurFade delay={0.02}>
          <ActivityHistoryList
            entries={groupedActivities}
            loading={loadingActivities}
            onDelete={setDeleteId}
          />
        </BlurFade>
      </CardContent>

      <AddActivityDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        targetId={targetMode === 'student' ? selectedStudentId : selectedGroupId}
        targetName={targetMode === 'student' ? (selectedStudent?.full_name || '') : (selectedGroup?.name || '')}
        mode={targetMode}
        onSuccess={() => {
          void loadAllActivities();
        }}
      />

      <DeleteActivityDialog
        open={!!deleteId}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteId(null);
          }
        }}
        onConfirm={handleDelete}
      />
    </Card>
  );
}
