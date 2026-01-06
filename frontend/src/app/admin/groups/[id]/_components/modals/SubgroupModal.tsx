'use client';

import { Button } from '@/components/ui/button';

interface SubgroupModalProps {
  open: boolean;
  subgroup: number | null;
  text: string;
  isAssigning: boolean;
  assignResult: { matched: number; not_found: string[] } | null;
  onTextChange: (text: string) => void;
  onSubmit: () => void;
  onClose: () => void;
}

export function SubgroupModal({
  open,
  subgroup,
  text,
  isAssigning,
  assignResult,
  onTextChange,
  onSubmit,
  onClose,
}: SubgroupModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card border rounded-xl p-6 w-full max-w-lg mx-4">
        <h3 className="text-lg font-semibold mb-2">
          Назначить подгруппу {subgroup}
        </h3>
        <p className="text-sm text-muted-foreground mb-4">
          Вставьте список ФИО студентов. Система найдёт их в группе и назначит подгруппу.
        </p>
        <textarea
          className="w-full h-64 p-3 border rounded-lg bg-background text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="1. Иванов Иван Иванович&#10;2. Петров Пётр Петрович&#10;3. Сидорова Анна Сергеевна"
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
          autoFocus
        />
        {assignResult && assignResult.not_found.length > 0 && (
          <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-sm font-medium text-destructive mb-1">Не найдены:</p>
            <ul className="text-sm text-destructive/80">
              {assignResult.not_found.map((name, i) => (
                <li key={i}>• {name}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="flex gap-2 mt-4">
          <Button variant="outline" className="flex-1" onClick={onClose}>
            Отмена
          </Button>
          <Button 
            className="flex-1" 
            onClick={onSubmit} 
            disabled={!text.trim() || isAssigning}
          >
            {isAssigning ? 'Назначение...' : 'Назначить'}
          </Button>
        </div>
      </div>
    </div>
  );
}
