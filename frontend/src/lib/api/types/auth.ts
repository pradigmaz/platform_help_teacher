import { z } from 'zod';

export const UserSchema = z.object({
  id: z.string(),
  full_name: z.string(),
  username: z.string().optional(),
  role: z.enum(['student', 'teacher', 'admin']),
});

export type User = z.infer<typeof UserSchema>;

export const AuthResponseSchema = z.object({
  message: z.string(),
  user: UserSchema,
});

export type AuthResponse = z.infer<typeof AuthResponseSchema>;

export function validateResponse<T>(schema: z.ZodSchema<T>, data: unknown): T {
  return schema.parse(data);
}
