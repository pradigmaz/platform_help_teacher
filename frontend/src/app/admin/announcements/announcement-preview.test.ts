import { describe, expect, it } from 'vitest';

import { getAnnouncementPreview } from './announcement-preview';

describe('getAnnouncementPreview', () => {
  it('strips markdown syntax into readable preview text', () => {
    const markdown = [
      '## Что добавлено',
      '- Просмотр активных устройств',
      '- **Завершить все кроме текущей**',
      '- Нельзя завершить текущую сессию',
      '',
      '[Подробнее](https://example.com)',
    ].join('\n');

    expect(getAnnouncementPreview(markdown)).toBe(
      'Что добавлено • Просмотр активных устройств • Завершить все кроме текущей • Нельзя завершить текущую сессию Подробнее',
    );
  });
});
