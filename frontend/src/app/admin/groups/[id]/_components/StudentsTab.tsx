'use client';

import Link from 'next/link';
import { Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { StudentInGroup } from '@/lib/api/types';

interface StudentsTabProps {
  students: StudentInGroup[];
  searchQuery: string;
  onDeleteStudent: (id: string, name: string) => void;
}

export function StudentsTab({ students, searchQuery, onDeleteStudent }: StudentsTabProps) {
  const filteredStudents = students
    .filter(student => student.full_name.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => a.full_name.localeCompare(b.full_name, 'ru'));

  return (
    <div className="border rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground w-12">#</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">ФИО</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Username</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Действия</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {filteredStudents.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                {searchQuery ? 'Студенты не найдены' : 'В группе пока нет студентов'}
              </td>
            </tr>
          ) : (
            filteredStudents.map((student, idx) => (
              <tr key={student.id} className="hover:bg-muted/30">
                <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{idx + 1}</td>
                <td className="px-4 py-3">
                  <Link 
                    href={`/admin/students/${student.id}`}
                    className="font-medium text-primary hover:underline"
                  >
                    {student.full_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  {student.username ? `@${student.username}` : '—'}
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
  );
}
