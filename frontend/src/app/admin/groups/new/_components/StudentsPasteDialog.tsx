import { Button } from '@/components/ui/button';

interface StudentsPasteDialogProps {
  open: boolean;
  text: string;
  onTextChange: (value: string) => void;
  onClose: () => void;
  onSubmit: () => void;
}

export function StudentsPasteDialog({
  open,
  text,
  onTextChange,
  onClose,
  onSubmit,
}: StudentsPasteDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card border rounded-xl p-6 w-full max-w-lg mx-4">
        <h3 className="text-lg font-semibold mb-4">Вставить список студентов</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Вставьте список ФИО, каждое имя на новой строке. Нумерация будет удалена автоматически.
        </p>
        <textarea
          className="w-full h-64 p-3 border rounded-lg bg-background text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="1. Иванов Иван Иванович&#10;2. Петров Пётр Петрович&#10;3. Сидорова Анна Сергеевна"
          value={text}
          onChange={(event) => onTextChange(event.target.value)}
          autoFocus
        />
        <div className="flex gap-2 mt-4">
          <Button variant="outline" className="flex-1" onClick={onClose}>
            Отмена
          </Button>
          <Button className="flex-1" onClick={onSubmit} disabled={!text.trim()}>
            Добавить
          </Button>
        </div>
      </div>
    </div>
  );
}
