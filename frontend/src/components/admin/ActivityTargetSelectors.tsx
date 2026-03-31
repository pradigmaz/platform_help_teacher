'use client';

import { Plus, User, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { GroupResponse } from '@/lib/api';

interface StudentOption {
  id: string;
  full_name: string;
}

interface ActivityTargetSelectorsProps {
  groups: GroupResponse[];
  selectedGroupId: string;
  selectedStudentId: string;
  students: StudentOption[];
  loadingStudents: boolean;
  onGroupChange: (value: string) => void;
  onStudentChange: (value: string) => void;
  onOpenAddDialog: () => void;
}

export function ActivityTargetSelectors({
  groups,
  selectedGroupId,
  selectedStudentId,
  students,
  loadingStudents,
  onGroupChange,
  onStudentChange,
  onOpenAddDialog,
}: ActivityTargetSelectorsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="space-y-2">
        <label className="text-sm font-medium flex items-center gap-2">
          <Users className="w-4 h-4 text-muted-foreground" />
          Группа
        </label>
        <Select value={selectedGroupId} onValueChange={onGroupChange}>
          <SelectTrigger className="h-10">
            <SelectValue placeholder="Выберите группу" />
          </SelectTrigger>
          <SelectContent className="max-h-60">
            {groups.map((group) => (
              <SelectItem key={group.id} value={group.id}>
                {group.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium flex items-center gap-2">
          <User className="w-4 h-4 text-muted-foreground" />
          Студент
        </label>
        <Select
          value={selectedStudentId}
          onValueChange={onStudentChange}
          disabled={!selectedGroupId || loadingStudents}
        >
          <SelectTrigger className="h-10">
            <SelectValue placeholder={loadingStudents ? 'Загрузка...' : 'Все студенты'} />
          </SelectTrigger>
          <SelectContent className="max-h-60">
            <SelectItem value="__all__">Все студенты группы</SelectItem>
            {students.map((student) => (
              <SelectItem key={student.id} value={student.id}>
                {student.full_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-end">
        <Button onClick={onOpenAddDialog} disabled={!selectedGroupId} className="w-full h-10">
          <Plus className="w-4 h-4 mr-2" />
          {selectedStudentId ? 'Студенту' : 'Группе'}
        </Button>
      </div>
    </div>
  );
}
