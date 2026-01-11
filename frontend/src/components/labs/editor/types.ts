import { SerializedEditorState } from 'lexical';

export interface LabVariant {
  number: number;
  description: string;
  content?: SerializedEditorState;
  test_data?: string;
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
  questions: string[];
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
