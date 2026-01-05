'use client';

import { useState, useEffect, useMemo } from 'react';
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

type ViewMode = 'by-group' | 'all-students';
type SortKey = 'name' | 'group' | 'total' | 'labs' | 'attendance' | 'activity';
type SortOrder = 'asc' | 'desc';

export default function AttestationScoresPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('by-group');
  const [attestationType, setAttestationType] = useState<AttestationType>('first');
  const [selectedGroupId, setSelectedGroupId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [data, setData] = useState<GroupAttestationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [groupsLoading, setGroupsLoading] = useState(true);
  
  const [selectedStudent, setSelectedStudent] = useState<AttestationResult | null>(null);
  const [detailSheetOpen, setDetailSheetOpen] = useState(false);

  // Load groups on mount
  useEffect(() => {
    const loadGroups = async () => {
      try {
        const groupsData = await GroupsAPI.list();
        setGroups(groupsData);
        if (groupsData.length > 0) {
          setSelectedGroupId(groupsData[0].id);
        }
      } catch {
        toast.error('Ошибка загрузки групп');
      } finally {
        setGroupsLoading(false);
      }
    };
    loadGroups();
  }, []);

  // Load attestation data
  useEffect(() => {
    const loadData = async () => {
      if (viewMode === 'by-group' && !selectedGroupId) return;
      
      setLoading(true);
      try {
        let result: GroupAttestationResult;
        if (viewMode === 'all-students') {
          result = await AttestationAPI.calculateAllStudents(attestationType);
        } else {
          result = await AttestationAPI.calculateGroup(selectedGroupId, attestationType);
        }
        setData(result);
      } catch {
        toast.error('Ошибка загрузки данных аттестации');
        setData(null);
      } finally {
        setLoading(false);
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

  const handleSortChange = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  const handleStudentClick = (student: AttestationResult) => {
    setSelectedStudent(student);
    setDetailSheetOpen(true);
  };

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
        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as ViewMode)}>
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
          <Select value={selectedGroupId} onValueChange={setSelectedGroupId}>
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
        <Tabs value={attestationType} onValueChange={(v) => setAttestationType(v as AttestationType)}>
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
            onChange={(e) => setSearchQuery(e.target.value)}
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
        onOpenChange={setDetailSheetOpen}
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
