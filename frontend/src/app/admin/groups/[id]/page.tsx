'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Users, Key, BarChart3, Plus, Sparkles, Upload, ClipboardPaste, FileText, Users2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/sonner';
import { GroupsAPI, GroupDetailResponse } from '@/lib/api';
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

type Tab = 'students' | 'subgroups' | 'codes' | 'stats';

export default function GroupDetailPage() {
  const params = useParams();
  const router = useRouter();
  const groupId = params.id as string;

  const [group, setGroup] = useState<GroupDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('students');
  const [searchQuery, setSearchQuery] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRegeneratingGroupCode, setIsRegeneratingGroupCode] = useState(false);
  const [studentToDelete, setStudentToDelete] = useState<{ id: string, name: string } | null>(null);
  
  // Activity Dialog State
  const [activityDialog, setActivityDialog] = useState<{
    open: boolean;
    targetId: string;
    targetName: string;
    mode: 'group' | 'student';
  }>({ open: false, targetId: '', targetName: '', mode: 'group' });

  // Add Student Dialog State
  const [addStudentDialog, setAddStudentDialog] = useState(false);
  const [newStudentName, setNewStudentName] = useState('');
  const [isAddingStudent, setIsAddingStudent] = useState(false);
  
  // Bulk Import State
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Subgroup State
  const [subgroupModal, setSubgroupModal] = useState<{ open: boolean; subgroup: number | null }>({ open: false, subgroup: null });
  const [subgroupText, setSubgroupText] = useState('');
  const [isAssigningSubgroup, setIsAssigningSubgroup] = useState(false);
  const [assignResult, setAssignResult] = useState<{ matched: number; not_found: string[] } | null>(null);

  useEffect(() => {
    loadGroup();
  }, [groupId]);

  const loadGroup = async () => {
    try {
      const data = await GroupsAPI.get(groupId);
      setGroup(data);
    } catch (e) {
      toast.error('Ошибка загрузки данных группы');
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  // Handlers
  const handleGenerateCodes = async () => {
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
  };

  const handleRegenerateCode = async (userId: string) => {
    try {
      await GroupsAPI.regenerateUserCode(userId);
      toast.success('Код обновлён');
      await loadGroup();
    } catch {
      toast.error('Ошибка при регенерации кода');
    }
  };

  const handleRegenerateGroupCode = async () => {
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
  };

  const handleDeleteStudent = async () => {
    if (!studentToDelete) return;
    try {
      await GroupsAPI.removeStudent(groupId, studentToDelete.id);
      toast.success('Студент удалён');
      await loadGroup();
    } catch {
      toast.error('Ошибка при удалении');
    } finally {
      setStudentToDelete(null);
    }
  };

  const handleAddStudent = async () => {
    if (!newStudentName.trim()) {
      toast.error('Введите ФИО студента');
      return;
    }
    setIsAddingStudent(true);
    try {
      await GroupsAPI.addStudent(groupId, { full_name: newStudentName.trim() });
      toast.success('Студент добавлен');
      setNewStudentName('');
      setAddStudentDialog(false);
      await loadGroup();
    } catch {
      toast.error('Ошибка при добавлении студента');
    } finally {
      setIsAddingStudent(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsImporting(true);
    try {
      const parsedData = await GroupsAPI.parseFile(file);
      for (const student of parsedData) {
        await GroupsAPI.addStudent(groupId, { full_name: student.full_name });
      }
      toast.success(`Добавлено студентов: ${parsedData.length}`);
      await loadGroup();
    } catch {
      toast.error('Ошибка при импорте файла');
    } finally {
      setIsImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const parseNames = (text: string): string[] => {
    const lines = text.split('\n').map(line => line.trim()).filter(Boolean);
    const names: string[] = [];
    for (const line of lines) {
      const cleaned = line.replace(/^\d+[\.\)\s]+/, '').trim();
      const name = cleaned.replace(/[^\p{L}\s-]/gu, ' ').replace(/\s+/g, ' ').trim();
      if (name && name.split(' ').length >= 2) {
        names.push(name);
      }
    }
    return names;
  };

  const handlePasteSubmit = async () => {
    const names = parseNames(pasteText);
    if (names.length === 0) {
      toast.error('Не удалось распознать имена');
      return;
    }
    setIsImporting(true);
    try {
      for (const name of names) {
        await GroupsAPI.addStudent(groupId, { full_name: name });
      }
      toast.success(`Добавлено студентов: ${names.length}`);
      setPasteText('');
      setShowPasteModal(false);
      await loadGroup();
    } catch {
      toast.error('Ошибка при добавлении');
    } finally {
      setIsImporting(false);
    }
  };

  const handleAssignSubgroup = async () => {
    const names = parseNames(subgroupText);
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
        setSubgroupModal({ open: false, subgroup: null });
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
  };

  const handleClearSubgroups = async () => {
    try {
      const result = await GroupsAPI.clearSubgroups(groupId);
      toast.success(`Подгруппы убраны у ${result.cleared} студентов`);
      await loadGroup();
    } catch {
      toast.error('Ошибка при очистке подгрупп');
    }
  };

  const handleOpenGroupActivity = () => {
    if (!group) return;
    setActivityDialog({ open: true, targetId: group.id, targetName: group.name, mode: 'group' });
  };

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
          <input type="file" ref={fileInputRef} className="hidden" accept=".xlsx,.xls,.docx,.txt,.csv" onChange={handleFileUpload} />
          <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={isImporting}>
            <Upload className="w-4 h-4 mr-2" /> {isImporting ? 'Импорт...' : 'Импорт'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowPasteModal(true)}>
            <ClipboardPaste className="w-4 h-4 mr-2" /> Вставить
          </Button>
          <Button variant="outline" onClick={() => setAddStudentDialog(true)} className="gap-2">
            <Plus className="w-4 h-4" /> Добавить
          </Button>
          <Button variant="outline" onClick={() => router.push(`/admin/groups/${groupId}/reports`)} className="gap-2">
            <FileText className="w-4 h-4" /> Отчёты
          </Button>
          <Button onClick={handleOpenGroupActivity} className="gap-2">
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
        onClose={() => { setShowPasteModal(false); setPasteText(''); }}
      />

      <SubgroupModal
        open={subgroupModal.open}
        subgroup={subgroupModal.subgroup}
        text={subgroupText}
        isAssigning={isAssigningSubgroup}
        assignResult={assignResult}
        onTextChange={setSubgroupText}
        onSubmit={handleAssignSubgroup}
        onClose={() => { setSubgroupModal({ open: false, subgroup: null }); setSubgroupText(''); setAssignResult(null); }}
      />
    </div>
  );
}
