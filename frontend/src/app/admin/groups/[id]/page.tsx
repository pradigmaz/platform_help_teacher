'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Copy, RefreshCw, Key, Check, Users, Trash2, BarChart3, User, Plus, Sparkles, Upload, ClipboardPaste, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { GroupsAPI, GroupDetailResponse } from '@/lib/api';
import { Command, CommandInput } from '@/components/ui/command';
import { MagicCard } from '@/components/ui/magic-card';
import { DotPattern } from '@/components/ui/dot-pattern';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion, AnimatePresence } from 'motion/react';
import { AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { AddActivityDialog } from '@/components/admin/AddActivityDialog';

type Tab = 'students' | 'codes' | 'stats';

export default function GroupDetailPage() {
  const params = useParams();
  const router = useRouter();
  const groupId = params.id as string;

  const [group, setGroup] = useState<GroupDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('students');
  const [searchQuery, setSearchQuery] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [studentToDelete, setStudentToDelete] = useState<{ id: string, name: string } | null>(null);
  
  // Activity Dialog State
  const [activityDialog, setActivityDialog] = useState<{
    open: boolean;
    targetId: string;
    targetName: string;
    mode: 'group' | 'student';
  }>({
    open: false,
    targetId: '',
    targetName: '',
    mode: 'group'
  });

  // Add Student Dialog State
  const [addStudentDialog, setAddStudentDialog] = useState(false);
  const [newStudentName, setNewStudentName] = useState('');
  const [isAddingStudent, setIsAddingStudent] = useState(false);
  
  // Bulk Import State
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleGenerateCodes = async () => {
    setIsGenerating(true);
    try {
      const result = await GroupsAPI.generateCodes(groupId);
      toast.success(`Сгенерировано кодов: ${result.generated}`);
      await loadGroup();
    } catch (e) {
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
    } catch (e) {
      toast.error('Ошибка при регенерации кода');
    }
  };

  const handleDeleteStudent = async () => {
    if (!studentToDelete) return;
    try {
      await GroupsAPI.removeStudent(groupId, studentToDelete.id);
      toast.success('Студент удалён');
      await loadGroup();
    } catch (e) {
      toast.error('Ошибка при удалении');
    } finally {
      setStudentToDelete(null);
    }
  };
  
  const handleOpenGroupActivity = () => {
    if (!group) return;
    setActivityDialog({
      open: true,
      targetId: group.id,
      targetName: group.name,
      mode: 'group'
    });
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
    } catch (e) {
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
      // Добавляем каждого студента
      for (const student of parsedData) {
        await GroupsAPI.addStudent(groupId, { full_name: student.full_name });
      }
      toast.success(`Добавлено студентов: ${parsedData.length}`);
      await loadGroup();
    } catch (e) {
      toast.error('Ошибка при импорте файла');
    } finally {
      setIsImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handlePasteSubmit = async () => {
    const lines = pasteText.split('\n').map(line => line.trim()).filter(Boolean);
    const names: string[] = [];
    
    for (const line of lines) {
      const cleaned = line.replace(/^\d+[\.\)\s]+/, '').trim();
      const name = cleaned.replace(/[^\p{L}\s-]/gu, ' ').replace(/\s+/g, ' ').trim();
      if (name && name.split(' ').length >= 2) {
        names.push(name);
      }
    }
    
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
    } catch (e) {
      toast.error('Ошибка при добавлении');
    } finally {
      setIsImporting(false);
    }
  };

  const handleOpenStudentActivity = (studentId: string, studentName: string) => {
    setActivityDialog({
      open: true,
      targetId: studentId,
      targetName: studentName,
      mode: 'student'
    });
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto p-8">
        {/* Header Skeleton */}
        <div className="flex items-center gap-4 mb-6">
          <Skeleton className="w-10 h-10 rounded-md" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>

        {/* Tabs Skeleton */}
        <div className="flex gap-4 border-b mb-6 pb-2">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-24" />
        </div>

        {/* Table Skeleton */}
        <div className="border rounded-xl overflow-hidden">
          <div className="bg-muted/50 h-12 w-full" />
          <div className="divide-y">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="px-4 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1">
                  <Skeleton className="h-4 w-8" />
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-8 w-8 rounded-md" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="p-8 text-center">
        <p className="text-muted-foreground">Группа не найдена</p>
        <Button variant="outline" className="mt-4" onClick={() => router.back()}>Назад</Button>
      </div>
    );
  }

  const filteredStudents = group.students.filter(student =>
    student.full_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const studentsWithoutCode = group.students.filter(s => !s.invite_code).length;

  return (
    <div className="relative min-h-screen max-w-6xl mx-auto p-8 overflow-hidden">
      <DotPattern
        className="[mask-image:radial-gradient(800px_circle_at_center,white,transparent)] opacity-40"
      />
      
      {/* Header */}
      <div className="relative flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push('/admin/groups')}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{group.name}</h1>
            <p className="text-muted-foreground">
              Код: <code className="bg-muted px-2 py-0.5 rounded font-mono">{group.code}</code>
              <span className="mx-2">•</span>
              {group.students.length} студентов
            </p>
          </div>
        </div>
        
        <div className="flex gap-2">
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            accept=".xlsx,.xls,.docx,.txt,.csv"
            onChange={handleFileUpload}
          />
          <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={isImporting}>
            <Upload className="w-4 h-4 mr-2" /> {isImporting ? 'Импорт...' : 'Импорт'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowPasteModal(true)}>
            <ClipboardPaste className="w-4 h-4 mr-2" /> Вставить
          </Button>
          <Button variant="outline" onClick={() => setAddStudentDialog(true)} className="gap-2">
            <Plus className="w-4 h-4" />
            Добавить
          </Button>
          <Button variant="outline" onClick={() => router.push(`/admin/groups/${groupId}/reports`)} className="gap-2">
            <FileText className="w-4 h-4" />
            Отчёты
          </Button>
          <Button onClick={handleOpenGroupActivity} className="gap-2">
            <Sparkles className="w-4 h-4" />
            Активность
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(value: string) => setActiveTab(value as Tab)} className="mb-6">
        <TabsList className="grid w-fit grid-cols-3">
          <TabsTrigger value="students" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Студенты
          </TabsTrigger>
          <TabsTrigger value="codes" className="flex items-center gap-2">
            <Key className="w-4 h-4" />
            Инвайт-коды
          </TabsTrigger>
          <TabsTrigger value="stats" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Статистика
          </TabsTrigger>
        </TabsList>

        {/* Search */}
        {(activeTab === 'students' || activeTab === 'codes') && (
          <div className="mt-6 mb-6">
            <Command className="border rounded-lg shadow-sm">
              <CommandInput
                placeholder="Поиск студентов по ФИО..."
                value={searchQuery}
                onValueChange={setSearchQuery}
              />
            </Command>
          </div>
        )}
      </Tabs>

      {/* Tab Content with Animation */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'students' && (
            <div className="border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground w-12">#</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">ФИО</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Username</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredStudents.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                    {searchQuery ? 'Студенты не найдены' : 'В группе пока нет студентов'}
                  </td>
                </tr>
              ) : (
                filteredStudents.map((student, idx) => (
                  <tr key={student.id} className="hover:bg-muted/30">
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{idx + 1}</td>
                    <td className="px-4 py-3">
                      <Link 
                        href={`/admin/students/${student.id}`}
                        className="font-medium text-primary hover:underline"
                      >
                        {student.full_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {student.username ? `@${student.username}` : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button 
                          size="sm" 
                          variant="ghost" 
                          className="text-destructive hover:text-destructive"
                          onClick={() => setStudentToDelete({ id: student.id, name: student.full_name })}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
            </div>
          )}

          {activeTab === 'codes' && (
            <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-card border rounded-lg">
            <div>
              <p className="font-medium">Генерация инвайт-кодов</p>
              <p className="text-sm text-muted-foreground">
                Студентов без кода: <span className="font-medium text-orange-500">{studentsWithoutCode}</span>
              </p>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleGenerateCodes} disabled={isGenerating || studentsWithoutCode === 0}>
                <Key className="w-4 h-4 mr-2" />
                {isGenerating ? 'Генерация...' : 'Сгенерировать всем'}
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredStudents.length === 0 ? (
              <div className="col-span-full py-12 text-center text-muted-foreground border rounded-xl bg-card/50">
                {searchQuery ? 'Студенты не найдены' : 'В группе пока нет студентов'}
              </div>
            ) : (
              filteredStudents.map((student) => (
                <MagicCard
                  key={student.id}
                  className="p-4 flex flex-col gap-3"
                  gradientColor="rgba(59, 130, 246, 0.1)"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-primary/10 rounded-full">
                        <User className="w-4 h-4 text-primary" />
                      </div>
                      <div className="font-medium truncate max-w-[150px]" title={student.full_name}>
                        {student.full_name}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0"
                      onClick={() => handleRegenerateCode(student.id)}
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </Button>
                  </div>

                  <div className="mt-auto pt-3 border-t flex items-center justify-between">
                    {student.invite_code ? (
                      <>
                        <code className="bg-muted px-2 py-1 rounded font-mono text-sm text-primary font-bold">
                          {student.invite_code}
                        </code>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 gap-2"
                          onClick={() => copyToClipboard(student.invite_code!, student.id)}
                        >
                          {copiedId === student.id ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-green-500" />
                              <span>Ок</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Копировать</span>
                            </>
                          )}
                        </Button>
                      </>
                    ) : (
                      <span className="text-muted-foreground text-xs italic">Код не сгенерирован</span>
                    )}
                  </div>
                </MagicCard>
              ))
            )}
          </div>
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="text-center py-12 border rounded-xl">
              <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground">Статистика будет доступна позже</p>
              <p className="text-sm text-muted-foreground mt-1">Посещаемость, оценки, активность</p>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      <AlertDialog open={!!studentToDelete} onOpenChange={(open) => !open && setStudentToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить студента?</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить студента {`"${studentToDelete?.name}"`} из группы?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteStudent} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AddActivityDialog
        open={activityDialog.open}
        onOpenChange={(open) => setActivityDialog(prev => ({ ...prev, open }))}
        targetId={activityDialog.targetId}
        targetName={activityDialog.targetName}
        mode={activityDialog.mode}
        onSuccess={() => {
          // Optional: refresh stats if we show them
        }}
      />

      {/* Add Student Dialog */}
      <AlertDialog open={addStudentDialog} onOpenChange={setAddStudentDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Добавить студента</AlertDialogTitle>
            <AlertDialogDescription>
              Введите ФИО студента для добавления в группу
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <input
              type="text"
              value={newStudentName}
              onChange={(e) => setNewStudentName(e.target.value)}
              placeholder="Иванов Иван Иванович"
              className="w-full px-3 py-2 border rounded-md bg-background"
              onKeyDown={(e) => e.key === 'Enter' && handleAddStudent()}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setNewStudentName('')}>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleAddStudent} disabled={isAddingStudent || !newStudentName.trim()}>
              {isAddingStudent ? 'Добавление...' : 'Добавить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Paste Modal */}
      {showPasteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card border rounded-xl p-6 w-full max-w-lg mx-4">
            <h3 className="text-lg font-semibold mb-4">Вставить список студентов</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Вставьте список ФИО, каждое имя на новой строке. Нумерация будет удалена автоматически.
            </p>
            <textarea
              className="w-full h-64 p-3 border rounded-lg bg-background text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="1. Иванов Иван Иванович&#10;2. Петров Пётр Петрович&#10;3. Сидорова Анна Сергеевна"
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              autoFocus
            />
            <div className="flex gap-2 mt-4">
              <Button variant="outline" className="flex-1" onClick={() => { setShowPasteModal(false); setPasteText(''); }}>
                Отмена
              </Button>
              <Button className="flex-1" onClick={handlePasteSubmit} disabled={!pasteText.trim() || isImporting}>
                {isImporting ? 'Добавление...' : 'Добавить'}
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
