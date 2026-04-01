import type { SerializedEditorState } from 'lexical';

import { lexicalToMarkdown } from './lexical-markdown';

describe('lexicalToMarkdown', () => {
  it('serializes headings, paragraphs, links and formatting', () => {
    const state = {
      root: {
        type: 'root',
        version: 1,
        children: [
          {
            type: 'heading',
            tag: 'h2',
            children: [{ type: 'text', text: 'Заголовок', format: 0, version: 1 }],
            version: 1,
          },
          {
            type: 'paragraph',
            children: [
              { type: 'text', text: 'Текст ', format: 0, version: 1 },
              { type: 'text', text: 'жирный', format: 1, version: 1 },
              { type: 'text', text: ' и ', format: 0, version: 1 },
              {
                type: 'link',
                url: 'https://example.com',
                children: [{ type: 'text', text: 'ссылка', format: 0, version: 1 }],
                version: 1,
              },
            ],
            version: 1,
          },
        ],
      },
    } as unknown as SerializedEditorState;

    expect(lexicalToMarkdown(state)).toBe('## Заголовок\n\nТекст **жирный** и [ссылка](https://example.com)');
  });

  it('serializes lists, code and tables', () => {
    const state = {
      root: {
        type: 'root',
        version: 1,
        children: [
          {
            type: 'list',
            listType: 'bullet',
            children: [
              { type: 'listitem', children: [{ type: 'paragraph', children: [{ type: 'text', text: 'Первый', format: 0, version: 1 }], version: 1 }], version: 1 },
              { type: 'listitem', children: [{ type: 'paragraph', children: [{ type: 'text', text: 'Второй', format: 0, version: 1 }], version: 1 }], version: 1 },
            ],
            version: 1,
          },
          { type: 'code-block', language: 'ts', code: 'console.log(1);', caption: 'Пример', version: 1 },
          {
            type: 'table',
            children: [
              { type: 'tablerow', children: [
                { type: 'tablecell', children: [{ type: 'paragraph', children: [{ type: 'text', text: 'A', format: 0, version: 1 }], version: 1 }], version: 1 },
                { type: 'tablecell', children: [{ type: 'paragraph', children: [{ type: 'text', text: 'B', format: 0, version: 1 }], version: 1 }], version: 1 },
              ], version: 1 },
              { type: 'tablerow', children: [
                { type: 'tablecell', children: [{ type: 'paragraph', children: [{ type: 'text', text: '1', format: 0, version: 1 }], version: 1 }], version: 1 },
                { type: 'tablecell', children: [{ type: 'paragraph', children: [{ type: 'text', text: '2', format: 0, version: 1 }], version: 1 }], version: 1 },
              ], version: 1 },
            ],
            version: 1,
          },
        ],
      },
    } as unknown as SerializedEditorState;

    expect(lexicalToMarkdown(state)).toContain('- Первый\n- Второй');
    expect(lexicalToMarkdown(state)).toContain('> Пример\n```ts\nconsole.log(1);\n```');
    expect(lexicalToMarkdown(state)).toContain('| A | B |\n| --- | --- |\n| 1 | 2 |');
  });

  it('serializes images and math nodes', () => {
    const state = {
      root: {
        type: 'root',
        version: 1,
        children: [
          { type: 'lecture-image', src: 'https://img.test/a.png', altText: 'alt', caption: 'Подпись', version: 1 },
          { type: 'math', latex: 'a^2+b^2=c^2', displayMode: true, version: 1 },
        ],
      },
    } as unknown as SerializedEditorState;

    expect(lexicalToMarkdown(state)).toBe('![alt](https://img.test/a.png)\n\n_Подпись_\n\n$$\na^2+b^2=c^2\n$$');
  });
});
