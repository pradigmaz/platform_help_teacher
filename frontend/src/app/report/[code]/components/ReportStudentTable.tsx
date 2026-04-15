'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { AlertTriangle, ArrowDownUp, ChevronRight, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PublicReportData, PublicStudentData } from '@/lib/api';
import { buildStudentReportHref, type ReportAttestation } from '../reportNavigation';

interface ReportStudentTableProps {
  data: PublicReportData;
  students: PublicStudentData[];
  code: string;
  attestationType: ReportAttestation;
}
type SortKey = 'name' | 'total' | 'labs' | 'attendance';
type SortOrder = 'asc' | 'desc';

export function ReportStudentTable({ data, students, code, attestationType }: ReportStudentTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showOnlyAttention, setShowOnlyAttention] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  const filteredStudents = useMemo(() => {
    const prepared = students.filter((student) => {
      if (showOnlyAttention && !student.needs_attention) {
        return false;
      }

      if (!searchQuery) {
        return true;
      }

      return getStudentName(student, data.show_names).toLowerCase().includes(searchQuery.toLowerCase());
    });

    return prepared.sort((left, right) => compareStudents(left, right, sortKey, sortOrder, data.show_names));
  }, [students, showOnlyAttention, searchQuery, sortKey, sortOrder, data.show_names]);

  const toggleSort = (nextSortKey: SortKey) => {
    if (sortKey === nextSortKey) {
      setSortOrder((current) => current === 'asc' ? 'desc' : 'asc');
      return;
    }

    setSortKey(nextSortKey);
    setSortOrder('asc');
  };

  const getStudentHref = (studentId: string) => buildStudentReportHref(code, studentId, attestationType);
  return (
    <Card className="rounded-3xl border-border/60 shadow-sm">
      <CardHeader className="space-y-4 border-b border-border/60 bg-muted/20 pb-5">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <CardTitle className="text-2xl font-semibold tracking-tight">Студенты</CardTitle>
            <p className="text-sm text-muted-foreground">
              {filteredStudents.length} из {students.length} в текущем списке
            </p>
          </div>
          <div className="flex flex-col gap-3 md:flex-row md:items-center">
            <div className="relative min-w-[240px]">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder={data.show_names ? 'Поиск по имени студента' : 'Поиск по студенту'}
                className="pl-9"
              />
            </div>
            <label className="flex items-center gap-3 text-sm text-muted-foreground">
              <Switch
                checked={showOnlyAttention}
                onCheckedChange={(value) => setShowOnlyAttention(Boolean(value))}
              />
              <span>Только требующие внимания</span>
            </label>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {filteredStudents.length === 0 ? (
          <EmptyStudentState searchQuery={searchQuery} showOnlyAttention={showOnlyAttention} />
        ) : (
          <>
            <div className="md:hidden">
              <Accordion type="single" collapsible className="px-4 py-3">
                {filteredStudents.map((student) => (
                  <AccordionItem
                    key={student.id}
                    value={student.id}
                    className="mb-3 rounded-2xl border border-border/60 bg-background px-4 last:mb-0"
                  >
                    <AccordionTrigger className="py-4 hover:no-underline">
                      <div className="flex min-w-0 flex-1 items-start justify-between gap-3 text-left">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            {student.needs_attention && (
                              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-500" />
                            )}
                            <p className="truncate text-sm font-semibold text-foreground">
                              {getStudentName(student, data.show_names)}
                            </p>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2">
                            {typeof student.total_score === 'number' && (
                              <Badge variant="outline">{student.total_score.toFixed(1)} балла</Badge>
                            )}
                            {typeof student.attendance_rate === 'number' && (
                              <Badge variant="outline">{Math.round(student.attendance_rate)}% посещаемость</Badge>
                            )}
                            {data.has_subgroups && student.subgroup && (
                              <Badge variant="secondary">{student.subgroup} подгруппа</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-2">
                        <MobileMetric label="Общий балл" value={formatScore(student.total_score)} />
                        <MobileMetric label="Посещаемость" value={formatPercent(student.attendance_rate)} />
                        <MobileMetric
                          label="Лабораторные"
                          value={formatLabProgress(student.labs_completed, student.labs_total)}
                        />
                        {!data.is_early_semester && data.show_grades && (
                          <MobileMetric label="Итог" value={student.grade ?? '—'} />
                        )}
                      </div>
                      <Button asChild className="w-full" variant="outline">
                        <Link href={getStudentHref(student.id)}>
                          Открыть подробности
                          <ChevronRight className="ml-2 h-4 w-4" />
                        </Link>
                      </Button>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>

            <div className="hidden md:block">
              <div className="flex items-center justify-between gap-3 border-b border-border/60 px-6 py-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <ArrowDownUp className="h-4 w-4" />
                  <span>Сортировка таблицы</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  <SortButton active={sortKey === 'name'} onClick={() => toggleSort('name')}>Имя</SortButton>
                  {data.show_grades && (
                    <SortButton active={sortKey === 'total'} onClick={() => toggleSort('total')}>Балл</SortButton>
                  )}
                  {data.show_grades && (
                    <SortButton active={sortKey === 'labs'} onClick={() => toggleSort('labs')}>Лабы</SortButton>
                  )}
                  {data.show_attendance && (
                    <SortButton active={sortKey === 'attendance'} onClick={() => toggleSort('attendance')}>
                      Посещаемость
                    </SortButton>
                  )}
                </div>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-14">#</TableHead>
                    <TableHead>Студент</TableHead>
                    {data.show_grades && <TableHead>Общий балл</TableHead>}
                    {data.show_grades && <TableHead>Лабораторные</TableHead>}
                    {data.show_attendance && <TableHead>Посещаемость</TableHead>}
                    {data.show_grades && !data.is_early_semester && <TableHead>Итог</TableHead>}
                    <TableHead className="text-right">Действие</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredStudents.map((student, index) => (
                    <TableRow key={student.id} className={cn(student.needs_attention && 'bg-amber-500/5')}>
                      <TableCell className="text-muted-foreground">{index + 1}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          {student.needs_attention && <AlertTriangle className="h-4 w-4 text-amber-500" />}
                          <div className="space-y-1">
                            <p className="font-medium text-foreground">{getStudentName(student, data.show_names)}</p>
                            {data.has_subgroups && student.subgroup && (
                              <Badge variant="outline">{student.subgroup} подгруппа</Badge>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      {data.show_grades && <TableCell className="font-medium">{formatScore(student.total_score)}</TableCell>}
                      {data.show_grades && <TableCell>{formatLabProgress(student.labs_completed, student.labs_total)}</TableCell>}
                      {data.show_attendance && <TableCell>{formatPercent(student.attendance_rate)}</TableCell>}
                      {data.show_grades && !data.is_early_semester && <TableCell>{student.grade ?? '—'}</TableCell>}
                      <TableCell className="text-right">
                        <Button asChild variant="ghost">
                          <Link href={getStudentHref(student.id)}>
                            Открыть
                            <ChevronRight className="ml-2 h-4 w-4" />
                          </Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function compareStudents(
  left: PublicStudentData,
  right: PublicStudentData,
  sortKey: SortKey,
  sortOrder: SortOrder,
  showNames: boolean,
) {
  const direction = sortOrder === 'asc' ? 1 : -1;
  switch (sortKey) {
    case 'name':
      return getStudentName(left, showNames).localeCompare(getStudentName(right, showNames), 'ru') * direction;
    case 'total':
      return ((left.total_score ?? 0) - (right.total_score ?? 0)) * direction;
    case 'labs':
      return (((left.labs_completed ?? 0) / Math.max(left.labs_total ?? 1, 1)) - ((right.labs_completed ?? 0) / Math.max(right.labs_total ?? 1, 1))) * direction;
    case 'attendance':
      return ((left.attendance_rate ?? 0) - (right.attendance_rate ?? 0)) * direction;
  }
}

function getStudentName(student: PublicStudentData, showNames: boolean) {
  return showNames ? student.name ?? `Студент ${student.id.slice(0, 4)}` : `Студент ${student.id.slice(0, 4)}`;
}

function formatScore(score?: number) {
  return typeof score === 'number' ? score.toFixed(1) : '—';
}

function formatPercent(rate?: number) {
  return typeof rate === 'number' ? `${Math.round(rate)}%` : '—';
}

function formatLabProgress(completed?: number, total?: number) {
  return typeof completed === 'number' && typeof total === 'number' ? `${completed}/${total}` : '—';
}
function SortButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <Button variant={active ? 'secondary' : 'outline'} size="sm" onClick={onClick}>
      {children}
    </Button>
  );
}

function MobileMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/60 bg-muted/20 px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function EmptyStudentState({ searchQuery, showOnlyAttention }: { searchQuery: string; showOnlyAttention: boolean }) {
  return (
    <div className="flex min-h-[240px] flex-col items-center justify-center gap-3 px-6 py-10 text-center">
      <Search className="h-8 w-8 text-muted-foreground" />
      <div className="space-y-1">
        <p className="text-base font-medium text-foreground">Ничего не найдено</p>
        <p className="text-sm text-muted-foreground">
          {searchQuery || showOnlyAttention
            ? 'Попробуйте изменить поиск или отключить фильтр внимания.'
            : 'Список студентов пока пуст.'}
        </p>
      </div>
    </div>
  );
}
