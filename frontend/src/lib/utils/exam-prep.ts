import type { SerializedEditorState } from 'lexical';
import type { ExamPrepContentValue, ExamPrepQuestion } from '@/lib/api';
import { extractTextFromLexical } from './lexical-utils';

type ExamPrepValue = string | ExamPrepContentValue | null | undefined;

export const EMPTY_EXAM_PREP_EDITOR_STATE = {
  root: {
    children: [
      {
        type: 'paragraph',
        children: [],
        direction: null,
        format: '',
        indent: 0,
        version: 1,
      },
    ],
    direction: null,
    format: '',
    indent: 0,
    type: 'root',
    version: 1,
  },
} as unknown as SerializedEditorState;

function buildEditorStateFromText(text: string): SerializedEditorState {
  const normalized = text.trim();
  if (!normalized) {
    return EMPTY_EXAM_PREP_EDITOR_STATE;
  }

  return {
    root: {
      children: [
        {
          type: 'paragraph',
          children: [
            {
              detail: 0,
              format: 0,
              mode: 'normal',
              style: '',
              text: normalized,
              type: 'text',
              version: 1,
            },
          ],
          direction: null,
          format: '',
          indent: 0,
          version: 1,
        },
      ],
      direction: null,
      format: '',
      indent: 0,
      type: 'root',
      version: 1,
    },
  } as unknown as SerializedEditorState;
}

export function getExamPrepText(value: ExamPrepValue): string {
  if (!value) {
    return '';
  }
  if (typeof value === 'string') {
    return value.trim();
  }
  if (value.text?.trim()) {
    return value.text.trim();
  }
  if (value.content) {
    return extractTextFromLexical(value.content as unknown as SerializedEditorState);
  }
  return '';
}

export function hasExamPrepContent(value: ExamPrepValue): boolean {
  return getExamPrepText(value).length > 0;
}

export function toExamPrepEditorState(value: ExamPrepValue): SerializedEditorState {
  if (value && typeof value !== 'string' && value.content) {
    return value.content as unknown as SerializedEditorState;
  }
  return buildEditorStateFromText(getExamPrepText(value));
}

export function toExamPrepContentValue(content: SerializedEditorState | Record<string, unknown>): ExamPrepContentValue {
  const serializedContent = content as unknown as SerializedEditorState;
  return {
    text: extractTextFromLexical(serializedContent),
    content: content as unknown as Record<string, unknown>,
  };
}

function createQuestionId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `question-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function createEmptyExamPrepQuestion(): ExamPrepQuestion {
  return {
    id: createQuestionId(),
    prompt: {
      text: '',
      content: EMPTY_EXAM_PREP_EDITOR_STATE as unknown as Record<string, unknown>,
    },
    answer: null,
  };
}

export function moveExamPrepQuestion(questions: ExamPrepQuestion[], index: number, direction: -1 | 1) {
  const nextIndex = index + direction;
  if (nextIndex < 0 || nextIndex >= questions.length) {
    return questions;
  }

  const nextQuestions = [...questions];
  const [question] = nextQuestions.splice(index, 1);
  nextQuestions.splice(nextIndex, 0, question);
  return nextQuestions;
}

export function pickQuizQuestions(questions: ExamPrepQuestion[], limit = 10) {
  const shuffled = [...questions];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
  }
  return shuffled.slice(0, Math.min(limit, shuffled.length));
}
