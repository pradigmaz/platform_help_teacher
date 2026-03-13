import { z } from 'zod';

export const gradeCellSchema = z.object({
  grade: z.string()
    .refine(
      (val) => val === '' || /^[2-5]$/.test(val),
      'Только цифры'
    )
    .refine(
      (val) => val === '' || (parseInt(val) >= 2 && parseInt(val) <= 5),
      'Оценка от 2 до 5'
    ),
  work_number: z.number().min(1, 'Номер работы от 1').optional().nullable(),
});

export type GradeCellFormValues = z.infer<typeof gradeCellSchema>;
