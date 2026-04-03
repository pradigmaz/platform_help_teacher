'use client';

import { ArrowLeft, ClipboardPaste, FileText, Plus, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { GroupDetailResponse } from '@/lib/api';

interface GroupDetailHeaderProps {
  group: GroupDetailResponse;
  groupId: string;
  onBack: () => void;
  onOpenPasteModal: () => void;
  onOpenAddStudentDialog: () => void;
  onOpenReports: (groupId: string) => void;
  onOpenActivityDialog: () => void;
}

export function GroupDetailHeader({
  group,
  groupId,
  onBack,
  onOpenPasteModal,
  onOpenAddStudentDialog,
  onOpenReports,
  onOpenActivityDialog,
}: GroupDetailHeaderProps) {
  return (
    <div className="relative flex items-center justify-between mb-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{group.name}</h1>
          <p className="text-muted-foreground">{group.code} • {group.students.length} студентов</p>
        </div>
      </div>

      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={onOpenPasteModal}>
          <ClipboardPaste className="w-4 h-4 mr-2" /> Вставить
        </Button>
        <Button variant="outline" onClick={onOpenAddStudentDialog} className="gap-2">
          <Plus className="w-4 h-4" /> Добавить
        </Button>
        <Button variant="outline" onClick={() => onOpenReports(groupId)} className="gap-2">
          <FileText className="w-4 h-4" /> Отчёты
        </Button>
        <Button onClick={onOpenActivityDialog} className="gap-2">
          <Sparkles className="w-4 h-4" /> Активность
        </Button>
      </div>
    </div>
  );
}
