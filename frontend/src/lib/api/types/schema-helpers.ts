import type { components } from '../schema';

/**
 * Извлечь тип схемы по имени из OpenAPI schema.d.ts
 * 
 * @example
 * type User = Schema<'UserResponse'>;
 * type Group = Schema<'GroupResponse'>;
 * type Lab = Schema<'LabResponse'>;
 */
export type Schema<T extends keyof components['schemas']> = components['schemas'][T];
