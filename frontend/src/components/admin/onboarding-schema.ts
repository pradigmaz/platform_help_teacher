import { z } from 'zod';

export const onboardingSchema = z.object({
  fullName: z.string().min(1, 'Введите ФИО'),
  mode: z.enum(['auto', 'manual']),
  startDate: z.string().min(1, 'Выберите дату начала семестра'),
});

export type OnboardingFormValues = z.infer<typeof onboardingSchema>;

export const onboardingDefaults: OnboardingFormValues = {
  fullName: '',
  mode: 'auto',
  startDate: '2025-09-01',
};
