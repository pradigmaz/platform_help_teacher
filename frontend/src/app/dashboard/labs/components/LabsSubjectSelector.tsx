'use client';

import type { AttestationSubjectOption } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface LabsSubjectSelectorProps {
  subjects: AttestationSubjectOption[];
  selectedSubject: AttestationSubjectOption | null;
  selectedSubjectId: string | null;
  onSelectSubject: (subjectId: string) => void;
}

export function LabsSubjectSelector({ subjects, selectedSubject, selectedSubjectId, onSelectSubject }: LabsSubjectSelectorProps) {
  if (subjects.length === 0) return null;

  const isMultiSubject = subjects.length > 1;
  const description = isMultiSubject
    ? 'В группе несколько предметов. Лабораторные и пороги показываются только в выбранном контексте.'
    : 'Этот предмет выбран автоматически. Ниже показаны лабораторные только по нему.';

  return (
    <CardSpotlight className="p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-semibold text-foreground">{isMultiSubject ? 'Контекст предмета' : 'Текущий предмет'}</h2>
            {selectedSubject ? <Badge variant="secondary">{selectedSubject.name}</Badge> : null}
            {isMultiSubject ? <Badge variant="outline">{subjects.length} предмета</Badge> : null}
          </div>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        {isMultiSubject ? (
          <Select value={selectedSubjectId ?? ''} onValueChange={onSelectSubject}>
            <SelectTrigger className="w-full bg-background md:w-[280px]">
              <SelectValue placeholder="Предмет" />
            </SelectTrigger>
            <SelectContent>
              {subjects.map((subject) => (
                <SelectItem key={subject.id} value={subject.id}>
                  {subject.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : null}
      </div>
    </CardSpotlight>
  );
}
