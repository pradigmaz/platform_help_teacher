import { z } from 'zod';

export const feedbackSchema = z.object({
  type: z.enum(['bug', 'suggestion']),
  title: z.string().min(5, 'Минимум 5 символов').max(200, 'Максимум 200 символов'),
  description: z.string().min(20, 'Минимум 20 символов').max(10000),
});

export type FeedbackFormValues = z.infer<typeof feedbackSchema>;

export const feedbackDefaults: FeedbackFormValues = {
  type: 'bug',
  title: '',
  description: '',
};
