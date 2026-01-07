'use client';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { FlaskConical, Calendar, Eye, Pencil, Trash2 } from 'lucide-react';
import { BlurFade } from '@/components/ui/blur-fade';

interface Lab {
  id: string;
  title: string;
  description: string | null;
  max_grade: number;
  deadline: string | null;
  created_at: string;
}

interface LabsTableProps {
  labs: Lab[];
  onDelete: (id: string) => void;
}

export function LabsTable({ labs, onDelete }: LabsTableProps) {
  return (
    <BlurFade delay={0.35}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="w-5 h-5" />
            Список лабораторных
          </CardTitle>
          <CardDescription>Всего: {labs.length}</CardDescription>
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
                  <TableHead>Макс. балл</TableHead>
                  <TableHead>Дедлайн</TableHead>
                  <TableHead>Создано</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {labs.map((lab) => (
                  <TableRow key={lab.id} className="group hover:bg-muted/50">
                    <TableCell className="font-medium">{lab.title}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="bg-gradient-to-r from-purple-500/20 to-blue-500/20">
                        {lab.max_grade}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {lab.deadline ? (
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {new Date(lab.deadline).toLocaleDateString('ru-RU')}
                        </span>
                      ) : '—'}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(lab.created_at).toLocaleDateString('ru-RU')}
                    </TableCell>
                    <TableCell className="text-right space-x-1">
                      <Button variant="ghost" size="icon" asChild className="opacity-0 group-hover:opacity-100 transition-opacity">
                        <a href={`/admin/labs/${lab.id}`}>
                          <Eye className="h-4 w-4" />
                        </a>
                      </Button>
                      <Button variant="ghost" size="icon" asChild className="opacity-0 group-hover:opacity-100 transition-opacity">
                        <a href={`/admin/labs/${lab.id}/edit`}>
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
