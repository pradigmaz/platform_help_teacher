'use client';

import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
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
  studentSearch: string;
  onGroupChange: (id: string) => void;
  onSubjectChange: (id: string) => void;
  onLessonTypeChange: (type: string) => void;
  onStudentSearchChange: (query: string) => void;
}

export function JournalFilters({
  groups,
  subjects,
  selectedGroupId,
  selectedSubjectId,
  selectedLessonType,
  studentSearch,
  onGroupChange,
  onSubjectChange,
  onLessonTypeChange,
  onStudentSearchChange,
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

      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Поиск студента..."
          value={studentSearch}
          onChange={(e) => onStudentSearchChange(e.target.value)}
          className="pl-8 w-[180px] h-9"
        />
      </div>
    </>
  );
}
