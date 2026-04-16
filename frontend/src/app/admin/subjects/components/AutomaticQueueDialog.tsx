'use client';

import { ArrowRightLeft, Award, Clock3, UserRoundX } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { AutomaticQueueResponse, GroupSubjectOffering } from '@/lib/api';

interface AutomaticQueueDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  offering: GroupSubjectOffering | null;
  queue: AutomaticQueueResponse | null;
  loading: boolean;
  onDecline: (studentId: string) => void;
  onRestore: (studentId: string) => void;
}

function formatDateTime(value: string | null) {
  if (!value) {
    return '—';
  }
  return new Date(value).toLocaleString('ru-RU');
}

function getProgressValue(completedCount: number, totalLabs: number) {
  if (!totalLabs) {
    return 0;
  }
  return Math.min(100, Math.round((completedCount / totalLabs) * 100));
}

function getStatusBadge(row: AutomaticQueueResponse['students'][number], queue: AutomaticQueueResponse) {
  if (row.is_declined) {
    return <Badge variant="destructive">Отказ</Badge>;
  }
  if (row.is_winner) {
    return <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">Автомат</Badge>;
  }
  if (row.queue_position && queue.automatic_places && row.queue_position === queue.automatic_places + 1) {
    return <Badge className="bg-amber-500 text-black hover:bg-amber-500">Следующий</Badge>;
  }
  if (row.queue_position) {
    return <Badge variant="secondary">Очередь #{row.queue_position}</Badge>;
  }
  return <Badge variant="outline">Ещё {row.automatic_remaining}</Badge>;
}

function getStatusNote(row: AutomaticQueueResponse['students'][number], queue: AutomaticQueueResponse) {
  if (row.is_declined) {
    return row.declined_reason ? `Причина: ${row.declined_reason}` : 'Автомат снят администратором';
  }
  if (row.is_winner) {
    return 'Уже занимает место в квоте автомата';
  }
  if (row.queue_position && queue.automatic_places && row.queue_position === queue.automatic_places + 1) {
    return 'Получит место первым, если кто-то выше откажется';
  }
  if (row.queue_position) {
    return 'Все лабы закрыты, но места пока заняты';
  }
  return `До допуска в очередь не хватает ${row.automatic_remaining} лаб.`;
}

export function AutomaticQueueDialog({
  open,
  onOpenChange,
  offering,
  queue,
  loading,
  onDecline,
  onRestore,
}: AutomaticQueueDialogProps) {
  const winnersCount = queue?.students.filter((row) => row.is_winner).length ?? 0;
  const declinedCount = queue?.students.filter((row) => row.is_declined).length ?? 0;
  const eligibleCount = queue?.students.filter((row) => row.completed_count >= (queue?.total_labs ?? 0) && !row.is_declined).length ?? 0;
  const nextCandidate =
    queue?.students.find(
      (row) =>
        !row.is_declined &&
        !row.is_winner &&
        row.queue_position !== null &&
        queue.automatic_places !== null &&
        queue.automatic_places !== undefined &&
        row.queue_position === queue.automatic_places + 1,
    ) ?? null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full gap-0 overflow-hidden p-0 sm:max-w-5xl">
        <div className="flex h-full flex-col">
          <SheetHeader className="border-b border-border/60 px-6 py-5">
            <SheetTitle>
              Очередь автомата{offering ? `: ${offering.group_name} / ${offering.subject_name}` : ''}
            </SheetTitle>
            <SheetDescription>
              Здесь видно, кто уже занимает квоту, кто следующий после отказа и кому ещё не хватает лаб до допуска в очередь.
            </SheetDescription>
          </SheetHeader>

          {loading ? (
            <div className="px-6 py-10 text-center text-sm text-muted-foreground">Загрузка очереди…</div>
          ) : !queue ? (
            <div className="px-6 py-10 text-center text-sm text-muted-foreground">Нет данных</div>
          ) : (
            <div className="flex min-h-0 flex-1 flex-col">
              <div className="grid grid-cols-1 gap-3 border-b border-border/60 px-6 py-4 md:grid-cols-4">
                <div className="rounded-xl border border-border/60 bg-background/90 p-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Award className="h-4 w-4" />
                    Квота автомата
                  </div>
                  <div className="mt-2 text-2xl font-bold text-foreground">{queue.automatic_places ?? '—'}</div>
                  <div className="mt-1 text-xs text-muted-foreground">Сейчас занято: {winnersCount}</div>
                </div>
                <div className="rounded-xl border border-border/60 bg-background/90 p-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Clock3 className="h-4 w-4" />
                    Полностью закрыли
                  </div>
                  <div className="mt-2 text-2xl font-bold text-foreground">{eligibleCount}</div>
                  <div className="mt-1 text-xs text-muted-foreground">Из {queue.students.length} студентов группы</div>
                </div>
                <div className="rounded-xl border border-border/60 bg-background/90 p-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <ArrowRightLeft className="h-4 w-4" />
                    Следующий на место
                  </div>
                  <div className="mt-2 text-sm font-semibold text-foreground">
                    {nextCandidate ? nextCandidate.student_name : 'Пока нет'}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {nextCandidate?.queue_position ? `Очередь #${nextCandidate.queue_position}` : 'Некому передавать'}
                  </div>
                </div>
                <div className="rounded-xl border border-border/60 bg-background/90 p-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <UserRoundX className="h-4 w-4" />
                    Отказы
                  </div>
                  <div className="mt-2 text-2xl font-bold text-foreground">{declinedCount}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {queue.automatic_enabled ? 'При отказе место уходит следующему' : 'Глобально отключено'}
                  </div>
                </div>
              </div>

              <div className="min-h-0 flex-1 overflow-auto px-6 py-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[280px]">Студент</TableHead>
                      <TableHead className="w-[180px]">Прогресс</TableHead>
                      <TableHead className="w-[180px]">Последняя зачтённая</TableHead>
                      <TableHead className="w-[240px]">Статус автомата</TableHead>
                      <TableHead className="w-[140px] text-right">Действие</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {queue.students.map((row) => (
                      <TableRow key={row.student_id}>
                        <TableCell className="align-top">
                          <div className="space-y-1">
                            <div className="font-medium text-foreground">{row.student_name}</div>
                            {row.declined_reason ? (
                              <div className="text-xs text-muted-foreground">{row.declined_reason}</div>
                            ) : null}
                          </div>
                        </TableCell>
                        <TableCell className="align-top">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-xs text-muted-foreground">
                              <span>{row.completed_count}/{queue.total_labs}</span>
                              <span>{getProgressValue(row.completed_count, queue.total_labs)}%</span>
                            </div>
                            <Progress value={getProgressValue(row.completed_count, queue.total_labs)} className="h-2" />
                          </div>
                        </TableCell>
                        <TableCell className="align-top text-sm text-muted-foreground">
                          {formatDateTime(row.completion_at)}
                        </TableCell>
                        <TableCell className="align-top">
                          <div className="space-y-2">
                            {getStatusBadge(row, queue)}
                            <div className="text-xs text-muted-foreground">{getStatusNote(row, queue)}</div>
                          </div>
                        </TableCell>
                        <TableCell className="align-top text-right">
                          {row.is_declined ? (
                            <Button size="sm" variant="outline" onClick={() => onRestore(row.student_id)}>
                              Вернуть
                            </Button>
                          ) : row.completed_count >= queue.total_labs ? (
                            <Button size="sm" variant="outline" onClick={() => onDecline(row.student_id)}>
                              Отказать
                            </Button>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
