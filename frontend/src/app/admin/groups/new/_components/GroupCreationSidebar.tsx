import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface GroupCreationSidebarProps {
  step: 1 | 2;
  groupName: string;
  groupCode: string;
  studentsCount: number;
  isSubmitting: boolean;
  onNext: () => void;
  onBack: () => void;
  onSubmit: () => Promise<void>;
}

function StatusMark({ complete }: { complete: boolean }) {
  if (complete) {
    return <Check className="w-4 h-4 text-green-500" />;
  }

  return <div className="w-4 h-4 border rounded-full" />;
}

export function GroupCreationSidebar({
  step,
  groupName,
  groupCode,
  studentsCount,
  isSubmitting,
  onNext,
  onBack,
  onSubmit,
}: GroupCreationSidebarProps) {
  return (
    <div className="space-y-4">
      <div className="sticky top-8 space-y-4">
        <div className="p-4 border rounded-xl bg-card">
          <h3 className="font-semibold mb-2">Статус</h3>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center gap-2">
              <StatusMark complete={Boolean(groupName && groupCode)} />
              Данные группы
            </li>
            <li className="flex items-center gap-2">
              <StatusMark complete={studentsCount > 0} />
              Студенты ({studentsCount})
            </li>
          </ul>
        </div>

        {step === 1 ? (
          <Button className="w-full" size="lg" disabled={!groupName || !groupCode} onClick={onNext}>
            Далее: Студенты
          </Button>
        ) : (
          <div className="space-y-2">
            <Button
              className="w-full bg-green-600 hover:bg-green-700"
              size="lg"
              disabled={studentsCount === 0 || isSubmitting}
              onClick={() => {
                void onSubmit();
              }}
            >
              {isSubmitting ? 'Создание...' : 'Сохранить группу'}
            </Button>
            <Button variant="outline" className="w-full" onClick={onBack}>
              Назад
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
