'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Bug, Lightbulb, MessageSquarePlus } from 'lucide-react';
import { toast } from 'sonner';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import api from '@/lib/api';

const feedbackSchema = z.object({
  type: z.enum(['bug', 'suggestion']),
  title: z.string().min(5, 'Минимум 5 символов').max(200, 'Максимум 200 символов'),
  description: z.string().min(10, 'Опишите подробнее (минимум 10 символов)').max(5000),
});

type FeedbackForm = z.infer<typeof feedbackSchema>;

interface FeedbackDialogProps {
  trigger?: React.ReactNode;
}

export function FeedbackDialog({ trigger }: FeedbackDialogProps) {
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const form = useForm<FeedbackForm>({
    resolver: zodResolver(feedbackSchema),
    defaultValues: {
      type: 'bug',
      title: '',
      description: '',
    },
  });

  const onSubmit = async (data: FeedbackForm) => {
    try {
      setSubmitting(true);
      await api.post('/feedback', data);
      toast.success('Спасибо за обратную связь!');
      setOpen(false);
      form.reset();
    } catch {
      toast.error('Не удалось отправить');
    } finally {
      setSubmitting(false);
    }
  };

  const selectedType = form.watch('type');

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="ghost" size="icon" title="Обратная связь">
            <MessageSquarePlus className="h-5 w-5" />
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Обратная связь</DialogTitle>
          <DialogDescription>
            Сообщите об ошибке или предложите улучшение
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label>Тип обращения</Label>
            <RadioGroup
              value={selectedType}
              onValueChange={(v) => form.setValue('type', v as 'bug' | 'suggestion')}
              className="flex gap-4"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="bug" id="bug" />
                <Label htmlFor="bug" className="flex items-center gap-1 cursor-pointer">
                  <Bug className="h-4 w-4 text-red-500" />
                  Ошибка
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="suggestion" id="suggestion" />
                <Label htmlFor="suggestion" className="flex items-center gap-1 cursor-pointer">
                  <Lightbulb className="h-4 w-4 text-yellow-500" />
                  Предложение
                </Label>
              </div>
            </RadioGroup>
          </div>

          <div className="space-y-2">
            <Label htmlFor="title">Заголовок</Label>
            <Input
              id="title"
              placeholder={selectedType === 'bug' ? 'Кратко опишите проблему' : 'Суть предложения'}
              {...form.register('title')}
            />
            {form.formState.errors.title && (
              <p className="text-sm text-red-500">{form.formState.errors.title.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Описание</Label>
            <Textarea
              id="description"
              rows={5}
              placeholder={
                selectedType === 'bug'
                  ? 'Что произошло? Какие шаги привели к ошибке? Что ожидали увидеть?'
                  : 'Опишите вашу идею подробнее. Как это улучшит работу с системой?'
              }
              {...form.register('description')}
            />
            {form.formState.errors.description && (
              <p className="text-sm text-red-500">{form.formState.errors.description.message}</p>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Отправка...' : 'Отправить'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
