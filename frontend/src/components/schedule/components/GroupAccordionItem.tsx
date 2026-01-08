'use client';

import { ChevronDown, Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { NoteButton } from '@/components/notes';
import type { Student, AttendanceStatus, LectureGroup } from '../types';
import { ATTENDANCE_CONFIG } from '../constants';

interface GroupAccordionItemProps {
  group: LectureGroup;
  students: Student[];
  attendance: Record<string, AttendanceStatus | null>;
  isExpanded: boolean;
  isLoading: boolean;
  onToggle: () => void;
  onAttendanceClick: (studentId: string) => void;
}

export function GroupAccordionItem({
  group,
  students,
  attendance,
  isExpanded,
  isLoading,
  onToggle,
  onAttendanceClick,
}: GroupAccordionItemProps) {
  const presentCount = Object.values(attendance).filter(s => s === 'PRESENT' || s === 'LATE').length;
  const totalMarked = Object.values(attendance).filter(Boolean).length;

  return (
    <Collapsible open={isExpanded} onOpenChange={onToggle}>
      <div className={cn(
        'flex items-center justify-between p-3 rounded-lg border transition-colors',
        'hover:bg-muted/50 hover:border-primary/30',
        isExpanded ? 'bg-muted/30 border-primary/40' : 'border-border'
      )}>
        <CollapsibleTrigger className="flex items-center gap-3 flex-1">
          <Users className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{group.name}</span>
          {totalMarked > 0 && (
            <span className="text-xs text-muted-foreground">
              {presentCount}/{students.length}
            </span>
          )}
        </CollapsibleTrigger>
        <div className="flex items-center gap-2">
          <NoteButton entityType="lesson" entityId={group.lesson_id} size="sm" />
          <CollapsibleTrigger>
            <ChevronDown className={cn(
              'h-4 w-4 text-muted-foreground transition-transform',
              isExpanded && 'rotate-180'
            )} />
          </CollapsibleTrigger>
        </div>
      </div>
      
      <CollapsibleContent>
        <div className="border rounded-lg overflow-hidden mx-2 mb-2">
          {/* Table header */}
          <div className="grid grid-cols-[32px_1fr_32px_40px] gap-2 px-3 py-2 bg-muted text-[10px] font-medium text-muted-foreground uppercase">
            <span>#</span>
            <span>ФИО</span>
            <span></span>
            <span className="text-center">Посещ.</span>
          </div>

          {/* Rows */}
          <div className="divide-y">
            {isLoading ? (
              <div className="py-4 text-center text-sm text-muted-foreground">
                Загрузка...
              </div>
            ) : students.length === 0 ? (
              <div className="py-4 text-center text-sm text-muted-foreground">
                Нет студентов
              </div>
            ) : (
              students.map((student, idx) => {
                const att = attendance[student.id];
                const attConfig = att ? ATTENDANCE_CONFIG[att] : null;
                const AttIcon = attConfig?.icon;

                return (
                  <div
                    key={student.id}
                    className={cn(
                      'grid grid-cols-[32px_1fr_32px_40px] gap-2 px-3 py-2 items-center text-sm',
                      idx % 2 === 0 ? 'bg-background' : 'bg-muted/30'
                    )}
                  >
                    <span className="text-muted-foreground text-xs">{idx + 1}</span>
                    <span className="truncate" title={student.full_name}>{student.full_name}</span>
                    <NoteButton entityType="student" entityId={student.id} size="sm" />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onAttendanceClick(student.id);
                      }}
                      className={cn(
                        'h-7 w-7 rounded-full flex items-center justify-center transition-all hover:scale-110 mx-auto',
                        attConfig ? `${attConfig.color} ${attConfig.bg}` : 'text-muted-foreground/50 hover:bg-muted'
                      )}
                      title={attConfig?.label || 'Не отмечено'}
                    >
                      {AttIcon ? <AttIcon className="h-4 w-4" /> : <span>—</span>}
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
