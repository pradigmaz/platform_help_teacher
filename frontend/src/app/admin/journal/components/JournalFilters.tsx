'use client';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { Group, Subject } from '../lib/journal-constants';

interface JournalFiltersProps {
  groups: Group[];
  subjects: Subject[];
  selectedGroupId: string;
  selectedSubjectId: string;
  selectedLessonType: string;
  onGroupChange: (id: string) => void;
  onSubjectChange: (id: string) => void;
  onLessonTypeChange: (type: string) => void;
}

export function JournalFilters({
  groups,
  subjects,
  selectedGroupId,
  selectedSubjectId,
  selectedLessonType,
  onGroupChange,
  onSubjectChange,
  onLessonTypeChange,
}: JournalFiltersProps) {
  return (
    <>
      <Select value={selectedGroupId} onValueChange={onGroupChange}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Группа" />
        </SelectTrigger>
        <SelectContent>
          {groups.map(g => (
            <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={selectedSubjectId} onValueChange={onSubjectChange}>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Предмет" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все предметы</SelectItem>
          {subjects.map(s => (
            <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={selectedLessonType} onValueChange={onLessonTypeChange}>
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="Тип" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Все типы</SelectItem>
          <SelectItem value="lecture">Лекции</SelectItem>
          <SelectItem value="lab">Лабораторные</SelectItem>
          <SelectItem value="practice">Практики</SelectItem>
        </SelectContent>
      </Select>
    </>
  );
}
