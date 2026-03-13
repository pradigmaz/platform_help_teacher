'use client';
'use no memo';

import { useReducer, useEffect, useMemo, useCallback } from 'react';
import { toast } from 'sonner';
import { 
  api,
  AttestationAPI, 
  GroupsAPI, 
  AttestationResult,
  AttestationSubjectOption,
} from '@/lib/api';
import type { AttestationType } from '@/lib/api';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, Users, UserCheck } from 'lucide-react';
import { AttestationSummaryCards } from './components/SummaryCards';
import { AttestationTable } from './components/AttestationTable';
import { StudentDetailSheet } from './components/StudentDetailSheet';
import { AttestationContentSkeleton, AttestationPageSkeleton } from './components/PageSkeleton';
import { initialState, reducer, type SortKey, type ViewMode } from './state';

export default function AttestationScoresPage() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const {
    viewMode, attestationType, selectedGroupId, selectedSubjectId, searchQuery,
    sortKey, sortOrder, groups, availableSubjects, data, loading, groupsLoading,
    selectedStudent, detailSheetOpen
  } = state;

  // Load groups on mount
  useEffect(() => {
    const loadGroups = async () => {
      try {
        const groupsData = await GroupsAPI.list();
        dispatch({ type: 'SET_GROUPS', payload: groupsData });
      } catch {
        toast.error('Ошибка загрузки групп');
        dispatch({ type: 'SET_GROUPS_LOADING', payload: false });
      }
    };
    loadGroups();
  }, []);

  useEffect(() => {
    const loadSubjects = async () => {
      if (viewMode === 'by-group' && !selectedGroupId) {
        dispatch({ type: 'SET_AVAILABLE_SUBJECTS', payload: [] });
        return;
      }

      try {
        const subjects = viewMode === 'all-students'
          ? (await api.get<AttestationSubjectOption[]>('/admin/subjects/')).data
          : await AttestationAPI.listGroupSubjects(selectedGroupId, attestationType);

        dispatch({ type: 'SET_AVAILABLE_SUBJECTS', payload: subjects });

        if (subjects.length === 1 && selectedSubjectId !== subjects[0].id) {
          dispatch({ type: 'SET_SUBJECT_ID', payload: subjects[0].id });
          return;
        }

        if (subjects.every(subject => subject.id !== selectedSubjectId) && selectedSubjectId) {
          dispatch({ type: 'SET_SUBJECT_ID', payload: '' });
        }
      } catch {
        dispatch({ type: 'SET_AVAILABLE_SUBJECTS', payload: [] });
      }
    };

    loadSubjects();
  }, [viewMode, selectedGroupId, selectedSubjectId, attestationType]);

  const requiresExplicitSubject =
    viewMode === 'all-students' || availableSubjects.length > 1;
  const canLoadData =
    (viewMode === 'by-group' ? !!selectedGroupId : true) &&
    (!requiresExplicitSubject || !!selectedSubjectId);

  // Load attestation data
  useEffect(() => {
    const loadData = async () => {
      if (!canLoadData) {
        dispatch({ type: 'SET_DATA', payload: null });
        return;
      }
      
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        const result = viewMode === 'all-students'
          ? await AttestationAPI.calculateAllStudents(attestationType, selectedSubjectId)
          : await AttestationAPI.calculateGroup(selectedGroupId, attestationType, selectedSubjectId || undefined);
        dispatch({ type: 'SET_DATA', payload: result });
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : 'Ошибка загрузки';
        // Не показываем toast для "нет студентов" — это не ошибка
        if (!message.includes('нет активных студентов')) {
          toast.error(message);
        }
        dispatch({ type: 'SET_DATA', payload: null });
      }
    };
    loadData();
  }, [attestationType, canLoadData, selectedGroupId, selectedSubjectId, viewMode]);

  // Filter and sort students
  const filteredStudents = useMemo(() => {
    if (!data?.students) return [];
    
    return data.students
      .filter(s => s.student_name.toLowerCase().includes(searchQuery.toLowerCase()))
      .sort((a, b) => {
        const multiplier = sortOrder === 'asc' ? 1 : -1;
        switch (sortKey) {
          case 'name':
            return a.student_name.localeCompare(b.student_name, 'ru') * multiplier;
          case 'group':
            return (a.group_code || '').localeCompare(b.group_code || '', 'ru') * multiplier;
          case 'total':
            return (a.total_score - b.total_score) * multiplier;
          case 'labs':
            return (a.breakdown.labs_score - b.breakdown.labs_score) * multiplier;
          case 'attendance':
            return (a.breakdown.attendance_score - b.breakdown.attendance_score) * multiplier;
          case 'activity':
            return (a.breakdown.activity_score - b.breakdown.activity_score) * multiplier;
          default:
            return 0;
        }
      });
  }, [data?.students, searchQuery, sortKey, sortOrder]);

  // Handlers
  const handleSortChange = useCallback((key: SortKey) => {
    dispatch({ type: 'TOGGLE_SORT', payload: key });
  }, []);

  const handleStudentClick = useCallback((student: AttestationResult) => {
    dispatch({ type: 'OPEN_DETAIL', payload: student });
  }, []);

  const handleDetailSheetChange = useCallback((open: boolean) => {
    if (!open) dispatch({ type: 'CLOSE_DETAIL' });
  }, []);

  // Calculate summary from data
  const summary = useMemo(() => {
    if (!data) return null;
    const students = data.students || [];
    const scores = students.map(s => s.total_score);
    
    return {
      totalStudents: data.total_students,
      passedCount: data.passing_students,
      failedCount: data.failing_students,
      averageScore: data.average_score,
      minScore: scores.length > 0 ? Math.min(...scores) : 0,
      maxScore: scores.length > 0 ? Math.max(...scores) : 0,
      maxPoints: students[0]?.max_points || 40,
      minPassingPoints: students[0]?.min_passing_points || 18,
      gradeDistribution: data.grade_distribution || {},
    };
  }, [data]);

  if (groupsLoading) {
    return <AttestationPageSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Баллы аттестации</h1>
          <p className="text-muted-foreground">Просмотр и анализ баллов студентов</p>
        </div>
        
        {/* View Mode Tabs */}
        <Tabs value={viewMode} onValueChange={(v) => dispatch({ type: 'SET_VIEW_MODE', payload: v as ViewMode })}>
          <TabsList>
            <TabsTrigger value="by-group" className="gap-2">
              <Users className="h-4 w-4" />
              По группам
            </TabsTrigger>
            <TabsTrigger value="all-students" className="gap-2">
              <UserCheck className="h-4 w-4" />
              Все студенты
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Group Selector (only in by-group mode) */}
        {viewMode === 'by-group' && (
          <Select value={selectedGroupId} onValueChange={(v) => dispatch({ type: 'SET_GROUP_ID', payload: v })}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Выберите группу" />
            </SelectTrigger>
            <SelectContent>
              {groups.map(group => (
                <SelectItem key={group.id} value={group.id}>
                  {group.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        <Select
          value={selectedSubjectId}
          onValueChange={(v) => dispatch({ type: 'SET_SUBJECT_ID', payload: v })}
          disabled={availableSubjects.length === 0}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Выберите предмет" />
          </SelectTrigger>
          <SelectContent>
            {availableSubjects.map(subject => (
              <SelectItem key={subject.id} value={subject.id}>
                {subject.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Attestation Period Selector */}
        <Tabs value={attestationType} onValueChange={(v) => dispatch({ type: 'SET_ATTESTATION_TYPE', payload: v as AttestationType })}>
          <TabsList>
            <TabsTrigger value="first">1-я аттестация</TabsTrigger>
            <TabsTrigger value="second">2-я аттестация</TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-[300px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Поиск по ФИО..."
            value={searchQuery}
            onChange={(e) => dispatch({ type: 'SET_SEARCH', payload: e.target.value })}
            className="pl-9"
          />
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <AttestationContentSkeleton />
      ) : data && summary ? (
        <>
          <AttestationSummaryCards summary={summary} />
          <AttestationTable
            students={filteredStudents}
            viewMode={viewMode}
            sortKey={sortKey}
            sortOrder={sortOrder}
            onSortChange={handleSortChange}
            onStudentClick={handleStudentClick}
          />
        </>
      ) : (
        <div className="text-center py-12 text-muted-foreground">
          <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">
            {viewMode === 'by-group' && !selectedGroupId
              ? 'Выберите группу для просмотра баллов'
              : requiresExplicitSubject && !selectedSubjectId
                ? 'Выберите предмет для расчёта аттестации'
                : 'В группе нет активных студентов'}
          </p>
          <p className="text-sm mt-1">
            {viewMode === 'by-group' && selectedGroupId && !selectedSubjectId && availableSubjects.length > 1
              ? 'Аттестация теперь считается по предмету, без выбора предмета расчёт не выполняется'
              : viewMode === 'all-students' && !selectedSubjectId
                ? 'Для режима "Все студенты" нужен явный предмет'
                : viewMode === 'by-group' && selectedGroupId
                  ? 'Добавьте студентов в группу для расчёта аттестации'
                  : undefined}
          </p>
        </div>
      )}

      {/* Student Detail Sheet */}
      <StudentDetailSheet
        student={selectedStudent}
        open={detailSheetOpen}
        onOpenChange={handleDetailSheetChange}
        attestationType={attestationType}
      />
    </div>
  );
}
