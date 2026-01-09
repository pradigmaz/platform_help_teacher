'use client';

import { AttestationResult } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { cn } from '@/lib/utils';

type ViewMode = 'by-group' | 'all-students';
type SortKey = 'name' | 'group' | 'total' | 'labs' | 'attendance' | 'activity';
type SortOrder = 'asc' | 'desc';

interface AttestationTableProps {
  students: AttestationResult[];
  viewMode: ViewMode;
  sortKey: SortKey;
  sortOrder: SortOrder;
  onSortChange: (key: SortKey) => void;
  onStudentClick: (student: AttestationResult) => void;
}

export function AttestationTable({
  students,
  viewMode,
  sortKey,
  sortOrder,
  onSortChange,
  onStudentClick,
}: AttestationTableProps) {
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .slice(0, 2)
      .toUpperCase();
  };

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'отл': return 'bg-green-500/10 text-green-600 border-green-500/20';
      case 'хор': return 'bg-blue-500/10 text-blue-600 border-blue-500/20';
      case 'уд': return 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20';
      case 'неуд': return 'bg-red-500/10 text-red-600 border-red-500/20';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const getStatusBadge = (isPassing: boolean) => {
    return isPassing ? (
      <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
        Зачёт
      </Badge>
    ) : (
      <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
        Незачёт
      </Badge>
    );
  };

  if (students.length === 0) {
    return (
      <Card className="p-12 text-center text-muted-foreground">
        Нет студентов для отображения
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <SortableHeader
              label="Студент"
              sortKey="name"
              currentKey={sortKey}
              order={sortOrder}
              onClick={onSortChange}
            />
            {viewMode === 'all-students' && (
              <SortableHeader
                label="Группа"
                sortKey="group"
                currentKey={sortKey}
                order={sortOrder}
                onClick={onSortChange}
              />
            )}
            <SortableHeader
              label="Лабы"
              sortKey="labs"
              currentKey={sortKey}
              order={sortOrder}
              onClick={onSortChange}
              className="text-center"
            />
            <SortableHeader
              label="Посещ."
              sortKey="attendance"
              currentKey={sortKey}
              order={sortOrder}
              onClick={onSortChange}
              className="text-center"
            />
            <SortableHeader
              label="Актив."
              sortKey="activity"
              currentKey={sortKey}
              order={sortOrder}
              onClick={onSortChange}
              className="text-center"
            />
            <SortableHeader
              label="ИТОГО"
              sortKey="total"
              currentKey={sortKey}
              order={sortOrder}
              onClick={onSortChange}
              className="text-center"
            />
            <TableHead>Оценка</TableHead>
            <TableHead>Статус</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students.map((student) => (
            <TableRow
              key={student.student_id}
              className="cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => onStudentClick(student)}
            >
              {/* Student with avatar and progress */}
              <TableCell>
                <div className="flex items-center gap-3">
                  <Avatar className="h-9 w-9">
                    <AvatarFallback className="text-xs bg-primary/10 text-primary">
                      {getInitials(student.student_name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0">
                    <p className="font-medium truncate">{student.student_name}</p>
                    <Progress
                      value={(student.total_score / student.max_points) * 100}
                      className={cn(
                        "h-1.5 w-24 mt-1",
                        student.is_passing ? "[&>div]:bg-green-500" : "[&>div]:bg-red-500"
                      )}
                    />
                  </div>
                </div>
              </TableCell>

              {/* Group (only in all-students mode) */}
              {viewMode === 'all-students' && (
                <TableCell className="text-muted-foreground">
                  {student.group_code || '—'}
                </TableCell>
              )}

              {/* Scores */}
              <TableCell className="text-center font-mono text-sm">
                {student.breakdown.labs_score.toFixed(1)}
              </TableCell>
              <TableCell className="text-center font-mono text-sm">
                {student.breakdown.attendance_score.toFixed(1)}
              </TableCell>
              <TableCell className="text-center font-mono text-sm">
                {student.breakdown.activity_score.toFixed(1)}
              </TableCell>

              {/* Total */}
              <TableCell className="text-center">
                <span className="font-semibold text-lg">{student.total_score.toFixed(1)}</span>
                <span className="text-muted-foreground text-sm">/{student.max_points}</span>
              </TableCell>

              {/* Grade */}
              <TableCell>
                <Badge variant="outline" className={getGradeColor(student.grade)}>
                  {student.grade}
                </Badge>
              </TableCell>

              {/* Status */}
              <TableCell>
                {getStatusBadge(student.is_passing)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}

interface SortableHeaderProps {
  label: string;
  sortKey: SortKey;
  currentKey: SortKey;
  order: SortOrder;
  onClick: (key: SortKey) => void;
  className?: string;
}

function SortableHeader({ label, sortKey, currentKey, order, onClick, className }: SortableHeaderProps) {
  const isActive = sortKey === currentKey;
  
  return (
    <TableHead
      className={cn("cursor-pointer select-none hover:bg-muted/50 transition-colors", className)}
      onClick={() => onClick(sortKey)}
    >
      <div className="flex items-center gap-1 justify-center">
        <span>{label}</span>
        {isActive ? (
          order === 'asc' ? (
            <ArrowUp className="h-3 w-3" />
          ) : (
            <ArrowDown className="h-3 w-3" />
          )
        ) : (
          <ArrowUpDown className="h-3 w-3 opacity-30" />
        )}
      </div>
    </TableHead>
  );
}
