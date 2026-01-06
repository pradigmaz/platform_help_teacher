import type { TeacherContacts } from './reports';

export type ContactVisibility = 'student' | 'report' | 'both' | 'none';

export interface ContactVisibilitySettings {
  telegram: ContactVisibility;
  vk: ContactVisibility;
  max: ContactVisibility;
}

export interface TeacherContactsData {
  contacts: TeacherContacts;
  visibility: ContactVisibilitySettings;
}

export interface TeacherContactsUpdate {
  contacts: TeacherContacts;
  visibility: ContactVisibilitySettings;
}

export interface RelinkTelegramResponse {
  code: string;
  expires_in: number;
}

export interface StudentTeacherContacts {
  contacts: TeacherContacts | null;
  teacher_name?: string;
}
