'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { FlaskConical, Calendar, Eye, Pencil, Trash2, Plus } from 'lucide-react';
import { BlurFade } from '@/components/ui/blur-fade';
import type { Lab } from '@/lib/api/types/labs';
import type { AdminLabOfferingOption } from './subjectOptions';

interface LabsTableProps {
  labs: Lab[];
  offerings: AdminLabOfferingOption[];
  selectedOfferingId: string | null;
  onOfferingChange: (offeringId: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
}

export function LabsTable({ labs, offerings, selectedOfferingId, onOfferingChange, onCreate, onDelete }: LabsTableProps) {
  const selectedOffering = offerings.find((offering) => offering.id === selectedOfferingId) ?? null;
  const subjectQuery = selectedOffering
    ? `?subject_id=${selectedOffering.subjectId}&offering_id=${selectedOffering.id}`
    : '';

  return (
    <BlurFade delay={0.35}>
      <Card>
        <CardHeader className="gap-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FlaskConical className="w-5 h-5" />
                Список лабораторных
              </CardTitle>
              <CardDescription>Всего по предмету выбранной связки: {labs.length}</CardDescription>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
              <div className="min-w-0 space-y-1.5">
                <div className="text-sm font-medium">Группа / предмет</div>
                <Select value={selectedOfferingId ?? ''} onValueChange={onOfferingChange}>
                  <SelectTrigger className="w-full bg-background sm:w-[420px]">
                    <SelectValue placeholder="Выберите связку" />
                  </SelectTrigger>
                  <SelectContent>
                    {offerings.map((offering) => (
                      <SelectItem key={offering.id} value={offering.id}>
                        {offering.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={onCreate} disabled={!selectedOfferingId}>
                <Plus className="mr-2 h-4 w-4" />
                Создать лабу
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {labs.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <FlaskConical className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg">Нет лабораторных работ</p>
              <p className="text-sm">Создайте первую лабораторную работу</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Название</TableHead>
                  <TableHead>Дедлайн (5)</TableHead>
                  <TableHead>Дедлайн (4)</TableHead>
                  <TableHead>Создано</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {labs.map((lab) => (
                  <TableRow key={lab.id} className="group hover:bg-muted/50">
                    <TableCell className="font-medium">{lab.title}</TableCell>
                    <TableCell>
                      {lab.deadline_5_lessons ? (
                        <span className="flex items-center gap-1 text-sm">
                          <Calendar className="w-3 h-3" />
                          {lab.deadline_5_lessons} {lab.deadline_5_lessons === 1 ? 'пара' : lab.deadline_5_lessons < 5 ? 'пары' : 'пар'}
                        </span>
                      ) : '—'}
                    </TableCell>
                    <TableCell>
                      {lab.deadline_4_lessons ? (
                        <span className="flex items-center gap-1 text-sm">
                          <Calendar className="w-3 h-3" />
                          {lab.deadline_4_lessons} {lab.deadline_4_lessons === 1 ? 'пара' : lab.deadline_4_lessons < 5 ? 'пары' : 'пар'}
                        </span>
                      ) : '—'}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {lab.created_at ? new Date(lab.created_at).toLocaleDateString('ru-RU') : '—'}
                    </TableCell>
                    <TableCell className="text-right space-x-1">
                      <Button variant="ghost" size="icon" asChild className="opacity-0 group-hover:opacity-100 transition-opacity">
                        <a href={`/admin/labs/${lab.id}${subjectQuery}`}>
                          <Eye className="h-4 w-4" />
                        </a>
                      </Button>
                      <Button variant="ghost" size="icon" asChild className="opacity-0 group-hover:opacity-100 transition-opacity">
                        <a href={`/admin/labs/${lab.id}/edit${subjectQuery}`}>
                          <Pencil className="h-4 w-4" />
                        </a>
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => onDelete(lab.id)} className="opacity-0 group-hover:opacity-100 transition-opacity">
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </BlurFade>
  );
}
