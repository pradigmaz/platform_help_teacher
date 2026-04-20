import { describe, expect, it } from 'vitest';
import { createEmptyExamPrepQuestion, getExamPrepText, pickQuizQuestions } from './exam-prep';

describe('exam-prep utils', () => {
  it('extracts text from plain and rich content values', () => {
    expect(getExamPrepText('  TCP/IP  ')).toBe('TCP/IP');
    expect(
      getExamPrepText({
        content: {
          root: {
            children: [
              {
                type: 'paragraph',
                children: [
                  { text: 'OSI model', type: 'text', detail: 0, format: 0, mode: 'normal', style: '', version: 1 },
                ],
              },
            ],
          },
        },
      }),
    ).toBe('OSI model');
  });

  it('creates non-empty question ids and limits quiz sample size', () => {
    const questions = Array.from({ length: 12 }, (_, index) => ({
      id: `q-${index}`,
      prompt: `Вопрос ${index}`,
    }));

    expect(createEmptyExamPrepQuestion().id).toBeTruthy();
    expect(pickQuizQuestions(questions, 10)).toHaveLength(10);
  });
});
