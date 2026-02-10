import { z } from 'zod';

const noteColors = ['default', 'red', 'orange', 'yellow', 'green', 'blue', 'purple'] as const;

export const noteSchema = z.object({
  text: z.string().min(1, 'Текст обязателен').max(500, 'Максимум 500 символов'),
  color: z.enum(noteColors),
});

export type NoteFormValues = z.infer<typeof noteSchema>;

export const noteDefaults: NoteFormValues = {
  text: '',
  color: 'default',
};
