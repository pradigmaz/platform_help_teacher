import { z } from 'zod';

export const headerTabSchema = z.object({
  number: z.number().min(1, 'Номер должен быть больше 0'),
  title: z.string().min(1, 'Название обязательно'),
  goal: z.string().optional(),
  formatting_guide: z.string().optional(),
  deadline_5_lessons: z.number().min(1).max(4).nullable().optional(),
  deadline_4_lessons: z.number().min(2).max(5).nullable().optional(),
  is_sequential: z.boolean().optional(),
});

export type HeaderTabFormValues = z.infer<typeof headerTabSchema>;
