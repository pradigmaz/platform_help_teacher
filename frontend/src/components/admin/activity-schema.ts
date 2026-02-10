import { z } from 'zod';

export const activitySchema = z.object({
  points: z.number().min(-100, 'Минимум -100 баллов').max(100, 'Максимум 100 баллов'),
  description: z.string().min(1, 'Введите описание'),
  attestationType: z.enum(['first', 'second']),
});

export type ActivityFormValues = z.infer<typeof activitySchema>;

export const activityDefaults: ActivityFormValues = {
  points: 0.5,
  description: '',
  attestationType: 'first',
};
