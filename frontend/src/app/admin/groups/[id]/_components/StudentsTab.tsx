'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Trash2 } from 'lucide-react';
import { IconBrandTelegram, IconBrandVk } from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import type { StudentInGroup } from '@/lib/api/types';

interface StudentsTabProps {
  students: StudentInGroup[];
  searchQuery: string;
  onDeleteStudent: (id: string, name: string) => void;
  onDeleteStudentsBulk: (ids: string[]) => void;
}

export function StudentsTab({ students, searchQuery, onDeleteStudent, onDeleteStudentsBulk }: StudentsTabProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const filteredStudents = students
    .filter(student => student.full_name.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => a.full_name.localeCompare(b.full_name, 'ru'));

  const allSelected = filteredStudents.length > 0 && filteredStudents.every(s => selectedIds.has(s.id));
  const someSelected = selectedIds.size > 0;

  const toggleAll = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredStudents.map(s => s.id)));
    }
  };

  const toggleOne = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  };

  const handleBulkDelete = () => {
    if (selectedIds.size > 0) {
      onDeleteStudentsBulk(Array.from(selectedIds));
      setSelectedIds(new Set());
    }
  };

  return (
    <div className="space-y-3">
      {someSelected && (
        <div className="flex items-center gap-3 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
          <span className="text-sm">Выбрано: {selectedIds.size}</span>
          <Button size="sm" variant="destructive" onClick={handleBulkDelete}>
            <Trash2 className="w-4 h-4 mr-2" />
            Удалить выбранных
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setSelectedIds(new Set())}>
            Отменить
          </Button>
        </div>
      )}
      <div className="border rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left w-10">
                <Checkbox checked={allSelected} onCheckedChange={toggleAll} />
              </th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground w-12">#</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">ФИО</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Соцсети</th>
              <th className="px-4 py-3 text-right font-medium text-muted-foreground">Действия</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredStudents.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                  {searchQuery ? 'Студенты не найдены' : 'В группе пока нет студентов'}
                </td>
              </tr>
            ) : (
              filteredStudents.map((student, idx) => (
                <tr key={student.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <Checkbox 
                      checked={selectedIds.has(student.id)} 
                      onCheckedChange={() => toggleOne(student.id)} 
                    />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{idx + 1}</td>
                  <td className="px-4 py-3">
                    <Link 
                      href={`/admin/students/${student.id}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {student.full_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3 text-muted-foreground">
                      {student.username ? (
                        <span className="flex items-center gap-1" title="Telegram">
                          <IconBrandTelegram className="w-4 h-4 text-blue-500" />
                          @{student.username}
                        </span>
                      ) : null}
                      {student.vk_id ? (
                        <a 
                          href={`https://vk.com/id${student.vk_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 hover:text-blue-600"
                          title="ВКонтакте"
                        >
                          <IconBrandVk className="w-4 h-4 text-blue-600" />
                          VK
                        </a>
                      ) : null}
                      {!student.username && !student.vk_id && '—'}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button 
                      size="sm" 
                      variant="ghost" 
                      className="text-destructive hover:text-destructive"
                      onClick={() => onDeleteStudent(student.id, student.full_name)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
