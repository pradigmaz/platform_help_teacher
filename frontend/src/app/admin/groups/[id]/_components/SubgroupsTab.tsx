'use client';

import { Users2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { StudentInGroup } from '@/lib/api/types';

interface SubgroupsTabProps {
  students: StudentInGroup[];
  onAssignSubgroup: (subgroup: number) => void;
  onClearSubgroups: () => void;
}

export function SubgroupsTab({ students, onAssignSubgroup, onClearSubgroups }: SubgroupsTabProps) {
  const subgroup1 = students.filter(s => s.subgroup === 1);
  const subgroup2 = students.filter(s => s.subgroup === 2);
  const noSubgroup = students.filter(s => !s.subgroup);

  return (
    <div className="space-y-6">
      {/* Действия */}
      <div className="flex gap-2">
        <Button onClick={() => onAssignSubgroup(1)}>
          <Users2 className="w-4 h-4 mr-2" />
          Назначить подгруппу 1
        </Button>
        <Button onClick={() => onAssignSubgroup(2)} variant="outline">
          <Users2 className="w-4 h-4 mr-2" />
          Назначить подгруппу 2
        </Button>
        <Button onClick={onClearSubgroups} variant="ghost" className="text-muted-foreground">
          Убрать все подгруппы
        </Button>
      </div>

      {/* Две колонки */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Подгруппа 1 */}
        <div className="border rounded-xl p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <span className="bg-blue-500/20 text-blue-500 px-2 py-0.5 rounded text-sm">1</span>
            Подгруппа 1
            <span className="text-muted-foreground text-sm font-normal">({subgroup1.length})</span>
          </h3>
          <div className="space-y-1">
            {subgroup1.map((student, idx) => (
              <div key={student.id} className="flex items-center gap-2 py-1 text-sm">
                <span className="text-muted-foreground w-5">{idx + 1}.</span>
                <span>{student.full_name}</span>
              </div>
            ))}
            {subgroup1.length === 0 && (
              <p className="text-muted-foreground text-sm italic">Нет студентов</p>
            )}
          </div>
        </div>

        {/* Подгруппа 2 */}
        <div className="border rounded-xl p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <span className="bg-green-500/20 text-green-500 px-2 py-0.5 rounded text-sm">2</span>
            Подгруппа 2
            <span className="text-muted-foreground text-sm font-normal">({subgroup2.length})</span>
          </h3>
          <div className="space-y-1">
            {subgroup2.map((student, idx) => (
              <div key={student.id} className="flex items-center gap-2 py-1 text-sm">
                <span className="text-muted-foreground w-5">{idx + 1}.</span>
                <span>{student.full_name}</span>
              </div>
            ))}
            {subgroup2.length === 0 && (
              <p className="text-muted-foreground text-sm italic">Нет студентов</p>
            )}
          </div>
        </div>
      </div>

      {/* Без подгруппы */}
      {noSubgroup.length > 0 && (
        <div className="border rounded-xl p-4 bg-muted/30">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <span className="bg-muted text-muted-foreground px-2 py-0.5 rounded text-sm">—</span>
            Без подгруппы
            <span className="text-muted-foreground text-sm font-normal">({noSubgroup.length})</span>
          </h3>
          <div className="grid grid-cols-2 gap-x-4">
            {noSubgroup.map((student, idx) => (
              <div key={student.id} className="flex items-center gap-2 py-1 text-sm">
                <span className="text-muted-foreground w-5">{idx + 1}.</span>
                <span>{student.full_name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
