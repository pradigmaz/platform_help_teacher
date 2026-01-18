'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { 
  ArrowUpDown, 
  ArrowUp, 
  ArrowDown, 
  Search, 
  AlertTriangle,
  ChevronRight,
  Eye
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { PublicReportData } from '@/lib/api';

interface ReportStudentTableProps {
  data: PublicReportData;
  code: string;
}

type SortKey = 'name' | 'total' | 'labs' | 'attendance' | 'activity';
type SortOrder = 'asc' | 'desc';

// Вынесен за пределы компонента для React Compiler
function SortIcon({ columnKey, sortKey, sortOrder }: { columnKey: SortKey; sortKey: SortKey; sortOrder: SortOrder }) {
  if (sortKey !== columnKey) {
    return <ArrowUpDown className="h-5 w-5 ml-2 opacity-50" />;
  }
  return sortOrder === 'asc' 
    ? <ArrowUp className="h-5 w-5 ml-2" />
    : <ArrowDown className="h-5 w-5 ml-2" />;
}

export function ReportStudentTable({ data, code }: ReportStudentTableProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  const { show_names, show_grades, show_attendance, is_early_semester } = data;

  const filteredStudents = useMemo(() => {
    return data.students
      .filter(s => {
        if (!searchQuery) return true;
        const name = s.name || `Студент ${s.id.slice(0, 4)}`;
        return name.toLowerCase().includes(searchQuery.toLowerCase());
      })
      .sort((a, b) => {
        const multiplier = sortOrder === 'asc' ? 1 : -1;
        switch (sortKey) {
          case 'name':
            const nameA = a.name || `Студент ${a.id}`;
            const nameB = b.name || `Студент ${b.id}`;
            return nameA.localeCompare(nameB, 'ru') * multiplier;
          case 'total':
            return ((a.total_score || 0) - (b.total_score || 0)) * multiplier;
          case 'labs':
            return ((a.lab_score || 0) - (b.lab_score || 0)) * multiplier;
          case 'attendance':
            return ((a.attendance_rate || 0) - (b.attendance_rate || 0)) * multiplier;
          case 'activity':
            return ((a.activity_score || 0) - (b.activity_score || 0)) * multiplier;
          default:
            return 0;
        }
      });
  }, [data.students, searchQuery, sortKey, sortOrder]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  const handleStudentClick = (studentId: string) => {
    router.push(`/report/${code}/student/${studentId}`);
  };

  return (
    <Card className="shadow-lg">
      <CardHeader className="pb-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
          <CardTitle className="text-3xl font-bold text-gray-800 dark:text-gray-100">
            📚 Список студентов
          </CardTitle>
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Поиск по имени студента..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-12 text-base border-2 focus:border-blue-400 rounded-lg"
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-b-2 bg-gray-50 dark:bg-gray-800/50">
                <TableHead className="w-20 text-lg font-bold py-6 text-center">#</TableHead>
                <TableHead className="text-lg font-bold py-6">
                  <Button
                    variant="ghost"
                    size="lg"
                    className="-ml-3 h-12 text-lg font-semibold hover:bg-blue-100 dark:hover:bg-blue-900/30"
                    onClick={() => handleSort('name')}
                  >
                    {show_names ? '👤 ФИО студента' : '👤 Студент'}
                    <SortIcon columnKey="name" sortKey={sortKey} sortOrder={sortOrder} />
                  </Button>
                </TableHead>
                {show_grades && (
                  <>
                    <TableHead className="text-right text-lg font-bold py-6">
                      <Button
                        variant="ghost"
                        size="lg"
                        className="-mr-3 h-12 text-lg font-semibold hover:bg-blue-100 dark:hover:bg-blue-900/30"
                        onClick={() => handleSort('total')}
                      >
                        📊 Общий балл
                        <SortIcon columnKey="total" sortKey={sortKey} sortOrder={sortOrder} />
                      </Button>
                    </TableHead>
                    <TableHead className="hidden md:table-cell text-lg font-bold py-6">
                      <Button
                        variant="ghost"
                        size="lg"
                        className="-ml-3 h-12 text-lg font-semibold hover:bg-blue-100 dark:hover:bg-blue-900/30"
                        onClick={() => handleSort('labs')}
                      >
                        🧪 Лабораторные работы
                        <SortIcon columnKey="labs" sortKey={sortKey} sortOrder={sortOrder} />
                      </Button>
                    </TableHead>
                  </>
                )}
                {show_attendance && (
                  <TableHead className="hidden sm:table-cell text-lg font-bold py-6">
                    <Button
                      variant="ghost"
                      size="lg"
                      className="-ml-3 h-12 text-lg font-semibold hover:bg-blue-100 dark:hover:bg-blue-900/30"
                      onClick={() => handleSort('attendance')}
                    >
                      📅 Посещаемость
                      <SortIcon columnKey="attendance" sortKey={sortKey} sortOrder={sortOrder} />
                    </Button>
                  </TableHead>
                )}
                {show_grades && !is_early_semester && (
                  <TableHead className="text-center text-lg font-bold py-6">🎯 Итоговая оценка</TableHead>
                )}
                <TableHead className="w-40 text-lg font-bold py-6 text-center">Подробнее</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredStudents.map((student, index) => {
                // В начале семестра не показываем предупреждения
                const showWarning = student.needs_attention && !is_early_semester;
                
                return (
                <TableRow 
                  key={student.id}
                  className={cn(
                    "cursor-pointer transition-all duration-200 group hover:shadow-md",
                    showWarning 
                      ? "bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/20 dark:hover:bg-amber-950/30 border-l-4 border-amber-400" 
                      : "hover:bg-blue-50 dark:hover:bg-blue-950/20",
                    "h-16"
                  )}
                  onClick={() => handleStudentClick(student.id)}
                  onMouseEnter={() => setHoveredRow(student.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                >
                  <TableCell className="font-bold text-lg text-muted-foreground text-center">
                    {index + 1}
                  </TableCell>
                  <TableCell className="py-4">
                    <div className="flex items-center gap-3">
                      {showWarning && (
                        <AlertTriangle className="h-6 w-6 text-amber-500 flex-shrink-0 animate-pulse" />
                      )}
                      <div className="flex flex-col">
                        <span className={cn(
                          "font-semibold text-lg leading-tight",
                          showWarning && "text-amber-700 dark:text-amber-300"
                        )}>
                          {show_names 
                            ? student.name 
                            : `Студент ${student.id.slice(0, 4)}`}
                        </span>
                        {data.has_subgroups && student.subgroup && (
                          <Badge variant="outline" className="text-sm px-2 py-1 mt-1 w-fit">
                            {student.subgroup} подгруппа
                          </Badge>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  {show_grades && (
                    <>
                      <TableCell className="text-right font-mono font-bold text-xl py-4">
                        <span className="bg-blue-100 dark:bg-blue-900/30 px-3 py-1 rounded-lg">
                          {student.total_score?.toFixed(1) ?? '—'}
                        </span>
                      </TableCell>
                      <TableCell className="hidden md:table-cell py-4">
                        <LabProgressCell 
                          completed={student.labs_completed} 
                          total={student.labs_total}
                        />
                      </TableCell>
                    </>
                  )}
                  {show_attendance && (
                    <TableCell className="hidden sm:table-cell py-4">
                      <AttendanceCell rate={student.attendance_rate} />
                    </TableCell>
                  )}
                  {show_grades && !is_early_semester && (
                    <TableCell className="text-center py-4">
                      <GradeBadge 
                        grade={student.grade} 
                        isPassing={student.is_passing} 
                      />
                    </TableCell>
                  )}
                  <TableCell className="py-4">
                    <div className={cn(
                      "flex items-center justify-center gap-2 text-base font-medium transition-all duration-200",
                      hoveredRow === student.id 
                        ? "opacity-100 text-blue-600 dark:text-blue-400" 
                        : "opacity-60 text-muted-foreground"
                    )}>
                      <Eye className="h-5 w-5" />
                      <span className="hidden lg:inline">Подробнее</span>
                      <ChevronRight className="h-5 w-5" />
                    </div>
                  </TableCell>
                </TableRow>
              );
              })}
              {filteredStudents.length === 0 && (
                <TableRow>
                  <TableCell 
                    colSpan={show_grades && show_attendance ? 7 : 4} 
                    className="text-center py-12 text-lg text-muted-foreground"
                  >
                    <div className="flex flex-col items-center gap-4">
                      <div className="text-4xl">🔍</div>
                      <div>
                        {searchQuery 
                          ? 'Студенты не найдены по вашему запросу' 
                          : 'Нет данных о студентах'}
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

// Lab progress with visual dots or progress bar
function LabProgressCell({ completed, total }: { completed?: number; total?: number }) {
  if (completed === undefined || total === undefined) {
    return <span className="text-muted-foreground text-lg">—</span>;
  }

  const percent = total > 0 ? (completed / total) * 100 : 0;
  
  // Use dots for small numbers, progress bar for larger
  if (total <= 8) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex gap-1">
          {Array.from({ length: total }).map((_, i) => (
            <div
              key={i}
              className={cn(
                "w-3 h-3 rounded-full",
                i < completed 
                  ? "bg-green-500 shadow-sm" 
                  : "bg-gray-200 dark:bg-gray-700"
              )}
            />
          ))}
        </div>
        <span className="ml-2 text-base font-semibold text-muted-foreground">
          {completed}/{total}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 min-w-[120px]">
      <Progress 
        value={percent} 
        className="h-3 flex-1"
      />
      <span className="text-base font-semibold text-muted-foreground whitespace-nowrap">
        {completed}/{total}
      </span>
    </div>
  );
}

// Attendance with color indicator dot
function AttendanceCell({ rate }: { rate?: number }) {
  if (rate === undefined) {
    return <span className="text-muted-foreground text-lg">—</span>;
  }

  const rounded = Math.round(rate);
  
  // Color based on attendance rate
  const dotColor = rate >= 80 
    ? "bg-green-500" 
    : rate >= 60 
      ? "bg-yellow-500" 
      : "bg-red-500";

  const textColor = rate >= 80 
    ? "text-green-600 dark:text-green-400" 
    : rate >= 60 
      ? "text-yellow-600 dark:text-yellow-400" 
      : "text-red-600 dark:text-red-400";

  return (
    <div className="flex items-center gap-3">
      <div className={cn("w-4 h-4 rounded-full shadow-sm", dotColor)} />
      <span className={cn("font-mono text-lg font-bold", textColor)}>
        {rounded}%
      </span>
    </div>
  );
}

function GradeBadge({ grade, isPassing }: { grade?: string; isPassing?: boolean }) {
  if (!grade) return <span className="text-muted-foreground text-lg">—</span>;

  const variant = isPassing ? 'default' : 'destructive';
  const className = cn(
    "text-lg font-bold px-4 py-2",
    grade === 'отл' && 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 border-green-300',
    grade === 'хор' && 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border-blue-300',
    grade === 'уд' && 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 border-yellow-300',
    grade === 'неуд' && 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 border-red-300',
  );

  return (
    <Badge variant={variant} className={className}>
      {grade}
    </Badge>
  );
}