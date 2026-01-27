import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';

type SubmitActionsProps = {
  submitting: boolean;
  feedbackCreated: boolean;
  isSubmitDisabled: boolean;
  onCancel: () => void;
};

export function SubmitActions({ submitting, feedbackCreated, isSubmitDisabled, onCancel }: SubmitActionsProps) {
  return (
    <div className="flex justify-end gap-2 pt-2">
      <Button type="button" variant="outline" onClick={onCancel} disabled={feedbackCreated}>
        Отмена
      </Button>
      <Button
        type="submit"
        disabled={isSubmitDisabled}
        className={feedbackCreated ? 'bg-green-600 hover:bg-green-600' : ''}
      >
        {feedbackCreated ? (
          <>
            <Check className="h-4 w-4 mr-1" />
            Отправлено!
          </>
        ) : submitting ? (
          'Отправка...'
        ) : (
          'Отправить'
        )}
      </Button>
    </div>
  );
}
