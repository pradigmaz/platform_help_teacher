'use client';

import { BookOpen } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { ReportSubjectOption } from '@/lib/api';

interface SubjectSelectionCardProps {
  title: string;
  description: string;
  subjects: ReportSubjectOption[];
  value: string;
  onChange: (value: string) => void;
}

export function SubjectSelectionCard({
  title,
  description,
  subjects,
  value,
  onChange,
}: SubjectSelectionCardProps) {
  return (
    <Card className="border-border/60 shadow-sm">
      <CardContent className="space-y-4 p-5">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground">
            <BookOpen className="h-4 w-4" />
            <span>{title}</span>
          </div>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>

        <Select value={value} onValueChange={onChange}>
          <SelectTrigger className="max-w-sm">
            <SelectValue placeholder="Выберите предмет" />
          </SelectTrigger>
          <SelectContent>
            {subjects.map((subject) => (
              <SelectItem key={subject.id} value={subject.id}>
                {subject.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardContent>
    </Card>
  );
}
