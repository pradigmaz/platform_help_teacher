import { cn } from '@/lib/utils';

interface GroupBasicsStepProps {
  step: 1 | 2;
  groupName: string;
  groupCode: string;
  onGroupNameChange: (value: string) => void;
  onGroupCodeChange: (value: string) => void;
}

export function GroupBasicsStep({
  step,
  groupName,
  groupCode,
  onGroupNameChange,
  onGroupCodeChange,
}: GroupBasicsStepProps) {
  return (
    <div className={cn('p-6 border rounded-xl bg-card', step !== 1 && 'opacity-50 pointer-events-none')}>
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs">1</span>
        Основные данные
      </h2>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Название группы</label>
          <input
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="Например: ИС-24-1"
            value={groupName}
            onChange={(event) => onGroupNameChange(event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Код группы</label>
          <input
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="IS-24-1"
            value={groupCode}
            onChange={(event) => onGroupCodeChange(event.target.value.toUpperCase())}
          />
          <p className="text-xs text-muted-foreground">Уникальный код группы для идентификации.</p>
        </div>
      </div>
    </div>
  );
}
