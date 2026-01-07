'use client';

import { useReducer, useEffect, useMemo, useCallback } from 'react';
import { toast } from 'sonner';
import { 
  AttestationAPI, 
  GroupsAPI, 
  AttestationType, 
  GroupAttestationResult, 
  AttestationResult,
  GroupResponse 
} from '@/lib/api';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Search, Users, UserCheck } from 'lucide-react';
import { AttestationSummaryCards } from './components/SummaryCards';
import { AttestationTable } from './components/AttestationTable';
import { StudentDetailSheet } from './components/StudentDetailSheet';

// Types
type ViewMode = 'by-group' | 'all-students';
type SortKey = 'name' | 'group' | 'total' | 'labs' | 'attendance' | 'activity';
type SortOrder = 'asc' | 'desc';

interface State {
  // Filters
  viewMode: ViewMode;
  attestationType: AttestationType;
  selectedGroupId: string;
  searchQuery: string;
  // Sort
  sortKey: SortKey;
  sortOrder: SortOrder;
  // Data
  groups: GroupResponse[];
  data: GroupAttestationResult | null;
  // Loading
  loading: boolean;
  groupsLoading: boolean;
  // Detail sheet
  selectedStudent: AttestationResult | null;
  detailSheetOpen: boolean;
}

type Action =
  | { type: 'SET_VIEW_MODE'; payload: ViewMode }
  | { type: 'SET_ATTESTATION_TYPE'; payload: AttestationType }
  | { type: 'SET_GROUP_ID'; payload: string }
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'TOGGLE_SORT'; payload: SortKey }
  | { type: 'SET_GROUPS'; payload: GroupResponse[] }
  | { type: 'SET_DATA'; payload: GroupAttestationResult | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_GROUPS_LOADING'; payload: boolean }
  | { type: 'OPEN_DETAIL'; payload: AttestationResult }
  | { type: 'CLOSE_DETAIL' };

const initialState: State = {
  viewMode: 'by-group',
  attestationType: 'first',
  selectedGroupId: '',
  searchQuery: '',
  sortKey: 'name',
  sortOrder: 'asc',
  groups: [],
  data: null,
  loading: false,
  groupsLoading: true,
  selectedStudent: null,
  detailSheetOpen: false,
};

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_VIEW_MODE':
      return { ...state, viewMode: action.payload, searchQuery: '', data: null };
    case 'SET_ATTESTATION_TYPE':
      return { ...state, attestationType: action.payload };
    case 'SET_GROUP_ID':
      return { ...state, selectedGroupId: action.payload };
    case 'SET_SEARCH':
      return { ...state, searchQuery: action.payload };
    case 'TOGGLE_SORT':
      return state.sortKey === action.payload
        ? { ...state, sortOrder: state.sortOrder === 'asc' ? 'desc' : 'asc' }
        : { ...state, sortKey: action.payload, sortOrder: 'asc' };
    case 'SET_GROUPS':
      return { 
        ...state, 
        groups: action.payload,
        selectedGroupId: action.payload[0]?.id || '',
        groupsLoading: false 
      };
    case 'SET_DATA':
      return { ...state, data: action.payload, loading: false };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_GROUPS_LOADING':
      return { ...state, groupsLoading: action.payload };
    case 'OPEN_DETAIL':
      return { ...state, selectedStudent: action.payload, detailSheetOpen: true };
    case 'CLOSE_DETAIL':
      return { ...state, detailSheetOpen: false };
    default:
      return state;
  }
}

export default function AttestationScoresPage() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const {
    viewMode, attestationType, selectedGroupId, searchQuery,
    sortKey, sortOrder, groups, data, loading, groupsLoading,
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

  // Load attestation data
  useEffect(() => {
    const loadData = async () => {
      if (viewMode === 'by-group' && !selectedGroupId) return;
      
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        const result = viewMode === 'all-students'
          ? await AttestationAPI.calculateAllStudents(attestationType)
          : await AttestationAPI.calculateGroup(selectedGroupId, attestationType);
        dispatch({ type: 'SET_DATA', payload: result });
      } catch {
        toast.error('Ошибка загрузки данных аттестации');
        dispatch({ type: 'SET_DATA', payload: null });
      }
    };
    loadData();
  }, [viewMode, selectedGroupId, attestationType]);

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
            return (a.lab_score - b.lab_score) * multiplier;
          case 'attendance':
            return (a.attendance_score - b.attendance_score) * multiplier;
          case 'activity':
            return (a.activity_score - b.activity_score) * multiplier;
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
    return <PageSkeleton />;
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
        <ContentSkeleton />
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
          {viewMode === 'by-group' && !selectedGroupId 
            ? 'Выберите группу для просмотра баллов'
            : 'Нет данных для отображения'}
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

function PageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-10 w-64" />
      </div>
      <div className="flex gap-4">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-10 w-64" />
      </div>
      <ContentSkeleton />
    </div>
  );
}

function ContentSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}
      </div>
      <Skeleton className="h-96 rounded-xl" />
    </div>
  );
}
