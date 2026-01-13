import { SerializedEditorState } from 'lexical';
import { nanoid } from 'nanoid';

export interface LabVariant {
  id: string;
  number: number;
  description: string;
  content?: SerializedEditorState;
  test_data?: string;
}

export interface LabQuestion {
  id: string;
  content?: SerializedEditorState;
  text?: string; // legacy fallback
}

/** Создаёт новый вариант с уникальным ID */
export function createVariant(number: number): LabVariant {
  return { id: nanoid(), number, description: '', test_data: '' };
}

/** Создаёт новый вопрос с уникальным ID */
export function createQuestion(): LabQuestion {
  return { id: nanoid(), text: '' };
}

/** Нормализует legacy вопрос (string) в LabQuestion с ID */
export function normalizeQuestion(q: LabQuestion | string): LabQuestion {
  if (typeof q === 'string') {
    return { id: nanoid(), text: q };
  }
  // Добавляем ID если отсутствует (legacy данные)
  if (!q.id) {
    return { ...q, id: nanoid() };
  }
  return q;
}

/** Нормализует legacy вариант без ID */
export function normalizeVariant(v: Partial<LabVariant> & { number: number }): LabVariant {
  return {
    id: v.id || nanoid(),
    number: v.number,
    description: v.description || '',
    content: v.content,
    test_data: v.test_data || '',
  };
}

export interface LabData {
  id?: string;
  number: number;
  title: string;
  goal?: string;
  formatting_guide?: string;
  theory_content?: SerializedEditorState;
  practice_content?: SerializedEditorState;
  variants: LabVariant[];
  questions: (LabQuestion | string)[]; // string для legacy, LabQuestion для нового формата
  max_grade: number;
  deadline_5_lessons?: number | null;
  deadline_4_lessons?: number | null;
  is_sequential: boolean;
}

export interface LabEditorProps {
  initialData?: Partial<LabData>;
  onSave: (data: LabData) => Promise<void>;
  className?: string;
}

export type UpdateFieldFn = <K extends keyof LabData>(field: K, value: LabData[K]) => void;
