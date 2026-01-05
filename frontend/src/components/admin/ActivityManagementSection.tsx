'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sparkles, Plus, Loader2, Users, Trash2, History, User, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import { GroupsAPI, ActivitiesAPI, GroupResponse, ActivityWithStudentResponse, AttestationType } from '@/lib/api';
import { AddActivityDialog } from './AddActivityDialog';
import { BlurFade } from '@/components/ui/blur-fade';
import { cn } from '@/lib/utils';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface StudentOption {
  id: string;
  full_name: string;
}

interface ActivityManagementSectionProps {
  attestationType: AttestationType;
}

export function ActivityManagementSection({ attestationType }: ActivityManagementSectionProps) {
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<string>('');
  const [students, setStudents] = useState<StudentOption[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<string>('');
  const [allActivities, setAllActivities] = useState<ActivityWithStudentResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingActivities, setLoadingActivities] = useState(true);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [targetMode, setTargetMode] = useState<'group' | 'student'>('group');

  useEffect(() => {
    loadGroups();
    loadAllActivities();
  }, []);

  useEffect(() => {
    loadAllActivities();
  }, [attestationType]);

  useEffect(() => {
    if (selectedGroupId) {
      loadStudents(selectedGroupId);
    } else {
      setStudents([]);
      setSelectedStudentId('');
    }
  }, [selectedGroupId]);

  const loadGroups = async () => {
    try {
      const data = await GroupsAPI.list();
      setGroups(data);
    } catch (error) {
      toast.error('Не удалось загрузить группы');
    }
  };

  const loadStudents = async (groupId: string) => {
    setLoading(true);
    try {
      const group = await GroupsAPI.get(groupId);
      setStudents(group.students || []);
    } catch (error) {
      toast.error('Не удалось загрузить студентов');
    } finally {
      setLoading(false);
    }
  };

  const loadAllActivities = async () => {
    setLoadingActivities(true);
    try {
      const data = await ActivitiesAPI.getAll(attestationType, 100);
      setAllActivities(data);
    } catch (error) {
      toast.error('Не удалось загрузить активности');
    } finally {
      setLoadingActivities(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await ActivitiesAPI.delete(deleteId);
      toast.success('Активность удалена');
      loadAllActivities();
    } catch (error) {
      toast.error('Ошибка при удалении');
    } finally {
      setDeleteId(null);
    }
  };

  const handleAddSuccess = () => {
    loadAllActivities();
  };

  const selectedGroup = groups.find(g => g.id === selectedGroupId);
  const selectedStudent = students.find(s => s.id === selectedStudentId);

  // Группируем по batch_id для отображения групповых начислений
  const groupedActivities = allActivities.reduce((acc, act) => {
    if (act.batch_id) {
      if (!acc[act.batch_id]) {
        acc[act.batch_id] = [];
      }
      acc[act.batch_id].push(act);
    } else {
      acc[act.id] = [act];
    }
    return acc;
  }, {} as Record<string, ActivityWithStudentResponse[]>);

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
  };

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
        {/* Селекторы для добавления */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Users className="w-4 h-4 text-muted-foreground" />
              Группа
            </label>
            <Select value={selectedGroupId} onValueChange={setSelectedGroupId}>
              <SelectTrigger className="h-10">
                <SelectValue placeholder="Выберите группу" />
              </SelectTrigger>
              <SelectContent className="max-h-60">
                {groups.map(group => (
                  <SelectItem key={group.id} value={group.id}>
                    {group.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <User className="w-4 h-4 text-muted-foreground" />
              Студент
            </label>
            <Select 
              value={selectedStudentId} 
              onValueChange={(v) => setSelectedStudentId(v === '__all__' ? '' : v)}
              disabled={!selectedGroupId || loading}
            >
              <SelectTrigger className="h-10">
                <SelectValue placeholder={loading ? "Загрузка..." : "Все студенты"} />
              </SelectTrigger>
              <SelectContent className="max-h-60">
                <SelectItem value="__all__">Все студенты группы</SelectItem>
                {students.map(student => (
                  <SelectItem key={student.id} value={student.id}>
                    {student.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-end">
            <Button 
              onClick={() => {
                setTargetMode(selectedStudentId ? 'student' : 'group');
                setAddDialogOpen(true);
              }}
              disabled={!selectedGroupId}
              className="w-full h-10"
            >
              <Plus className="w-4 h-4 mr-2" />
              {selectedStudentId ? 'Студенту' : 'Группе'}
            </Button>
          </div>
        </div>

        <div className="border-t my-4" />

        {/* Список всех активностей */}
        <div>
          <h4 className="text-sm font-medium mb-4 flex items-center gap-2">
            <History className="w-4 h-4 text-muted-foreground" />
            История начислений
            {allActivities.length > 0 && (
              <Badge variant="secondary" className="ml-auto">
                {Object.keys(groupedActivities).length} записей
              </Badge>
            )}
          </h4>
          
          {loadingActivities ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
            </div>
          ) : Object.keys(groupedActivities).length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <History className="w-12 h-12 mx-auto mb-3 opacity-20" />
              <p className="text-sm">Нет записей для этой аттестации</p>
            </div>
          ) : (
            <ScrollArea className="h-[320px] pr-4">
              <div className="space-y-3">
                {Object.entries(groupedActivities).map(([key, acts], index) => {
                  const isGroup = acts.length > 1;
                  const first = acts[0];
                  const uniqueGroups = [...new Set(acts.map(a => a.group_name).filter(Boolean))];
                  
                  return (
                    <BlurFade key={key} delay={0.02 + index * 0.015}>
                      <div className={cn(
                        "group relative flex items-start gap-3 p-4 rounded-xl border transition-all",
                        "hover:bg-muted/50 hover:border-purple-500/20 hover:shadow-sm"
                      )}>
                        {/* Avatar / Icon */}
                        <div className={cn(
                          "h-10 w-10 shrink-0 rounded-full flex items-center justify-center text-xs font-medium",
                          first.points > 0 ? "bg-green-500/10 text-green-600" : "bg-red-500/10 text-red-600"
                        )}>
                          {isGroup ? (
                            <Users className="w-4 h-4" />
                          ) : (
                            getInitials(first.student_name || '??')
                          )}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0 space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge 
                              variant={first.points > 0 ? "default" : "destructive"}
                              className={cn(
                                "font-mono text-xs px-2",
                                first.points > 0 && "bg-green-500 hover:bg-green-600"
                              )}
                            >
                              {first.points > 0 ? '+' : ''}{first.points}
                            </Badge>
                            
                            {isGroup ? (
                              <span className="text-sm font-medium text-blue-500">
                                {uniqueGroups.join(', ')} 
                                <span className="text-muted-foreground font-normal ml-1">
                                  ({acts.length} чел.)
                                </span>
                              </span>
                            ) : (
                              <>
                                <span className="text-sm font-medium">{first.student_name}</span>
                                {first.group_name && (
                                  <Badge variant="outline" className="text-xs font-normal">
                                    {first.group_name}
                                  </Badge>
                                )}
                              </>
                            )}
                          </div>
                          
                          <p className="text-sm text-muted-foreground line-clamp-1">
                            {first.description}
                          </p>
                          
                          <div className="flex items-center gap-1 text-xs text-muted-foreground/70">
                            <Calendar className="w-3 h-3" />
                            {new Date(first.created_at).toLocaleDateString('ru-RU', {
                              day: 'numeric',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        </div>

                        {/* Delete button */}
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                          onClick={() => setDeleteId(first.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </BlurFade>
                  );
                })}
              </div>
            </ScrollArea>
          )}
        </div>
      </CardContent>

      <AddActivityDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        targetId={targetMode === 'student' ? selectedStudentId : selectedGroupId}
        targetName={targetMode === 'student' ? (selectedStudent?.full_name || '') : (selectedGroup?.name || '')}
        mode={targetMode}
        onSuccess={handleAddSuccess}
      />

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить активность?</AlertDialogTitle>
            <AlertDialogDescription>
              Это действие отменит начисление баллов.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}
