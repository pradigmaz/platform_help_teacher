import { z } from 'zod';

export const transferSchema = z.object({
  toGroupId: z.string().min(1, 'Выберите группу'),
  toSubgroup: z.string(),
  transferDate: z.string().min(1, 'Укажите дату перевода'),
  attestationType: z.enum(['first', 'second']),
});

export type TransferFormValues = z.infer<typeof transferSchema>;

export const transferDefaults: TransferFormValues = {
  toGroupId: '',
  toSubgroup: 'none',
  transferDate: new Date().toISOString().split('T')[0],
  attestationType: 'first',
};
