import { z } from 'zod';

const urlOrEmpty = z.string().refine(
  (val) => !val || val.startsWith('http://') || val.startsWith('https://') || val.startsWith('@'),
  { message: 'Должна быть ссылка или @username' }
);

const contactVisibility = z.enum(['student', 'report', 'both', 'none']);

export const contactsSchema = z.object({
  telegram: urlOrEmpty,
  telegram_visibility: contactVisibility,
  vk: urlOrEmpty,
  vk_visibility: contactVisibility,
  max: urlOrEmpty,
  max_visibility: contactVisibility,
});

export type ContactsFormValues = z.infer<typeof contactsSchema>;
