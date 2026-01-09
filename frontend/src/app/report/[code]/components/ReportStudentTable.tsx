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
    return <ArrowUpDown className="h-4 w-4 ml-1 opacity-50" />;
  }
  return sortOrder === 'asc' 
    ? <ArrowUp className="h-4 w-4 ml-1" />
    : <ArrowDown className="h-4 w-4 ml-1" />;
}

export function ReportStudentTable({ data, code }: ReportStudentTableProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  const { show_names, show_grades, show_attendance } = data;

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
    <Card>
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <CardTitle>Студенты</CardTitle>
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Поиск по имени..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="-ml-3 h-8"
                    onClick={() => handleSort('name')}
                  >
                    {show_names ? 'ФИО' : 'Студент'}
                    <SortIcon columnKey="name" sortKey={sortKey} sortOrder={sortOrder} />
                  </Button>
                </TableHead>
                {show_grades && (
                  <>
                    <TableHead className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="-mr-3 h-8"
                        onClick={() => handleSort('total')}
                      >
                        Баллы
                        <SortIcon columnKey="total" sortKey={sortKey} sortOrder={sortOrder} />
                      </Button>
                    </TableHead>
                    <TableHead className="hidden md:table-cell">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="-ml-3 h-8"
                        onClick={() => handleSort('labs')}
                      >
                        Лабы
                        <SortIcon columnKey="labs" sortKey={sortKey} sortOrder={sortOrder} />
                      </Button>
                    </TableHead>
                  </>
                )}
                {show_attendance && (
                  <TableHead className="hidden sm:table-cell">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="-ml-3 h-8"
                      onClick={() => handleSort('attendance')}
                    >
                      Посещ.
                      <SortIcon columnKey="attendance" sortKey={sortKey} sortOrder={sortOrder} />
                    </Button>
                  </TableHead>
                )}
                {show_grades && (
                  <TableHead className="text-center">Оценка</TableHead>
                )}
                <TableHead className="w-24"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredStudents.map((student, index) => (
                <TableRow 
                  key={student.id}
                  className={cn(
                    "cursor-pointer transition-colors group",
                    student.needs_attention 
                      ? "bg-red-500/5 hover:bg-red-500/10 dark:bg-red-500/10 dark:hover:bg-red-500/15" 
                      : "hover:bg-muted/50"
                  )}
                  onClick={() => handleStudentClick(student.id)}
                  onMouseEnter={() => setHoveredRow(student.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                >
                  <TableCell className="font-medium text-muted-foreground">
                    {index + 1}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {student.needs_attention && (
                        <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0 animate-pulse" />
                      )}
                      <span className={cn(
                        "font-medium",
                        student.needs_attention && "text-amber-700 dark:text-amber-400"
                      )}>
                        {show_names 
                          ? student.name 
                          : `Студент ${student.id.slice(0, 4)}`}
                      </span>
                    </div>
                  </TableCell>
                  {show_grades && (
                    <>
                      <TableCell className="text-right font-mono font-semibold">
                        {student.total_score?.toFixed(1) ?? '—'}
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <LabProgressCell 
                          completed={student.labs_completed} 
                          total={student.labs_total}
                        />
                      </TableCell>
                    </>
                  )}
                  {show_attendance && (
                    <TableCell className="hidden sm:table-cell">
                      <AttendanceCell rate={student.attendance_rate} />
                    </TableCell>
                  )}
                  {show_grades && (
                    <TableCell className="text-center">
                      <GradeBadge 
                        grade={student.grade} 
                        isPassing={student.is_passing} 
                      />
                    </TableCell>
                  )}
                  <TableCell>
                    <div className={cn(
                      "flex items-center gap-1 text-sm text-muted-foreground transition-opacity",
                      hoveredRow === student.id ? "opacity-100" : "opacity-0"
                    )}>
                      <Eye className="h-4 w-4" />
                      <span className="hidden lg:inline">Подробнее</span>
                      <ChevronRight className="h-4 w-4" />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {filteredStudents.length === 0 && (
                <TableRow>
                  <TableCell 
                    colSpan={show_grades && show_attendance ? 7 : 4} 
                    className="text-center py-8 text-muted-foreground"
                  >
                    {searchQuery 
                      ? 'Студенты не найдены' 
                      : 'Нет данных о студентах'}
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
    return <span className="text-muted-foreground">—</span>;
  }

  const percent = total > 0 ? (completed / total) * 100 : 0;
  
  // Use dots for small numbers, progress bar for larger
  if (total <= 8) {
    return (
      <div className="flex items-center gap-1">
        {Array.from({ length: total }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "w-2 h-2 rounded-full",
              i < completed 
                ? "bg-green-500" 
                : "bg-muted-foreground/20"
            )}
          />
        ))}
        <span className="ml-2 text-xs text-muted-foreground">
          {completed}/{total}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <Progress 
        value={percent} 
        className="h-2 flex-1"
      />
      <span className="text-xs text-muted-foreground whitespace-nowrap">
        {completed}/{total}
      </span>
    </div>
  );
}

// Attendance with color indicator dot
function AttendanceCell({ rate }: { rate?: number }) {
  if (rate === undefined) {
    return <span className="text-muted-foreground">—</span>;
  }

  const rounded = Math.round(rate);
  
  // Color based on attendance rate
  const dotColor = rate >= 80 
    ? "bg-green-500" 
    : rate >= 60 
      ? "bg-yellow-500" 
      : "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <div className={cn("w-2 h-2 rounded-full", dotColor)} />
      <span className={cn(
        "font-mono",
        rate >= 80 && "text-green-600 dark:text-green-400",
        rate >= 60 && rate < 80 && "text-yellow-600 dark:text-yellow-400",
        rate < 60 && "text-red-600 dark:text-red-400"
      )}>
        {rounded}%
      </span>
    </div>
  );
}

function GradeBadge({ grade, isPassing }: { grade?: string; isPassing?: boolean }) {
  if (!grade) return <span className="text-muted-foreground">—</span>;

  const variant = isPassing ? 'default' : 'destructive';
  const className = cn(
    grade === 'отл' && 'bg-green-500/10 text-green-600 dark:text-green-400 hover:bg-green-500/20',
    grade === 'хор' && 'bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20',
    grade === 'уд' && 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 hover:bg-yellow-500/20',
    grade === 'неуд' && 'bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-500/20',
  );

  return (
    <Badge variant={variant} className={className}>
      {grade}
    </Badge>
  );
}
