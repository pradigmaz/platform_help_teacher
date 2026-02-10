import { z } from 'zod';

export const backupSettingsSchema = z.object({
  enabled: z.boolean(),
  schedule_hour: z.number().int().min(0, 'Час должен быть от 0 до 23').max(23, 'Час должен быть от 0 до 23'),
  schedule_minute: z.number().int().min(0, 'Минуты должны быть от 0 до 59').max(59, 'Минуты должны быть от 0 до 59'),
  retention_days: z.number().int().min(1, 'Минимум 1 день'),
  max_backups: z.number().int().min(1, 'Минимум 1 бэкап'),
  notify_on_success: z.boolean(),
  notify_on_failure: z.boolean(),
});

export type BackupSettingsFormValues = z.infer<typeof backupSettingsSchema>;
