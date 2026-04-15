'use client';

import { useMemo, useState } from 'react';
import { Check, ChevronsUpDown } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';

export interface ExportStudentOption {
  id: string;
  full_name: string;
  subgroup: number | null;
}

interface ExportStudentPickerProps {
  students: ExportStudentOption[];
  value: string | null;
  onChange: (studentId: string | null) => void;
}

export function ExportStudentPicker({ students, value, onChange }: ExportStudentPickerProps) {
  const [open, setOpen] = useState(false);

  const selectedStudent = useMemo(
    () => students.find((student) => student.id === value) ?? null,
    [students, value],
  );

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          <span className="truncate">
            {selectedStudent ? selectedStudent.full_name : 'Все студенты'}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[360px] p-0" align="start">
        <Command shouldFilter>
          <CommandInput placeholder="Найти студента..." />
          <CommandList>
            <CommandEmpty>Студент не найден</CommandEmpty>
            <CommandItem
              value="all-students"
              onSelect={() => {
                onChange(null);
                setOpen(false);
              }}
            >
              <Check className={cn('mr-2 h-4 w-4', !selectedStudent ? 'opacity-100' : 'opacity-0')} />
              Все студенты
            </CommandItem>
            {students.map((student) => (
              <CommandItem
                key={student.id}
                value={`${student.full_name} ${student.subgroup ?? ''}`}
                onSelect={() => {
                  onChange(student.id);
                  setOpen(false);
                }}
              >
                <Check
                  className={cn('mr-2 h-4 w-4', selectedStudent?.id === student.id ? 'opacity-100' : 'opacity-0')}
                />
                <span className="truncate">{student.full_name}</span>
                {student.subgroup && (
                  <span className="ml-auto text-xs text-muted-foreground">
                    {student.subgroup} п.г.
                  </span>
                )}
              </CommandItem>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
