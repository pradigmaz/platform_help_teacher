import { z } from 'zod';

function getCurrentSemesterStart() {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();

  if (month >= 8) {
    return `${year}-09-01`;
  }

  return `${year}-02-01`;
}

export const onboardingSchema = z.object({
  fullName: z.string().min(1, 'Введите ФИО'),
  mode: z.enum(['auto', 'manual']),
  startDate: z.string(),
}).superRefine((values, ctx) => {
  if (values.mode === 'auto' && !values.startDate) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['startDate'],
      message: 'Выберите дату начала семестра',
    });
  }
});

export type OnboardingFormValues = z.infer<typeof onboardingSchema>;

export const onboardingDefaults: OnboardingFormValues = {
  fullName: '',
  mode: 'auto',
  startDate: getCurrentSemesterStart(),
};
