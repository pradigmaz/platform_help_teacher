import { z } from 'zod';

export const componentToggleSchema = z.object({
  weight: z.number().min(0, 'Вес не может быть отрицательным').max(100, 'Максимум 100%'),
});

export type ComponentToggleFormValues = z.infer<typeof componentToggleSchema>;
