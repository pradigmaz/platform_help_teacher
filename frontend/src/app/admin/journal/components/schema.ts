import { z } from 'zod';

export const gradeCellSchema = z.object({
  grade: z.string()
    .refine(
      (val) => val === '' || /^[0-9]{1,3}$/.test(val),
      'Только цифры'
    )
    .refine(
      (val) => val === '' || (parseInt(val) >= 0 && parseInt(val) <= 100),
      'Оценка от 0 до 100'
    ),
  work_number: z.number().min(1, 'Номер работы от 1').optional().nullable(),
});

export type GradeCellFormValues = z.infer<typeof gradeCellSchema>;
