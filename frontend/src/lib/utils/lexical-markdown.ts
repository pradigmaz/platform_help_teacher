import type { SerializedEditorState } from 'lexical';

type SerializedNode = {
  type?: string;
  text?: string;
  format?: number | string;
  url?: string;
  tag?: string;
  listType?: string;
  value?: number;
  src?: string;
  altText?: string;
  caption?: string;
  code?: string;
  language?: string;
  latex?: string;
  displayMode?: boolean;
  children?: SerializedNode[];
};

const FORMAT_BOLD = 1;
const FORMAT_ITALIC = 1 << 1;
const FORMAT_STRIKETHROUGH = 1 << 2;
const FORMAT_UNDERLINE = 1 << 3;
const FORMAT_CODE = 1 << 4;

function hasFormat(format: SerializedNode['format'], flag: number): boolean {
  return typeof format === 'number' ? (format & flag) !== 0 : false;
}

function wrapText(text: string, marker: string): string {
  return text ? `${marker}${text}${marker}` : text;
}

function serializeInline(node: SerializedNode): string {
  switch (node.type) {
    case 'text': {
      let text = node.text ?? '';
      if (!text) return '';
      if (hasFormat(node.format, FORMAT_CODE)) text = wrapText(text, '`');
      if (hasFormat(node.format, FORMAT_BOLD)) text = wrapText(text, '**');
      if (hasFormat(node.format, FORMAT_ITALIC)) text = wrapText(text, '_');
      if (hasFormat(node.format, FORMAT_STRIKETHROUGH)) text = wrapText(text, '~~');
      if (hasFormat(node.format, FORMAT_UNDERLINE)) text = `<u>${text}</u>`;
      return text;
    }
    case 'linebreak':
      return '  \n';
    case 'link': {
      const label = serializeInlineChildren(node).trim() || node.url || '';
      return node.url ? `[${label}](${node.url})` : label;
    }
    case 'math':
      return node.displayMode ? `$$\n${node.latex ?? ''}\n$$` : `$${node.latex ?? ''}$`;
    default:
      return serializeInlineChildren(node);
  }
}

function serializeInlineChildren(node: SerializedNode): string {
  return (node.children ?? []).map(serializeInline).join('');
}

function serializeParagraph(node: SerializedNode): string {
  return serializeInlineChildren(node).trim();
}

function serializeListItem(node: SerializedNode, ordered: boolean, depth: number, index: number): string {
  const indent = '  '.repeat(depth);
  const marker = ordered ? `${node.value ?? index + 1}. ` : '- ';
  const blocks: string[] = [];
  const nested: string[] = [];

  for (const child of node.children ?? []) {
    if (child.type === 'list') {
      nested.push(serializeList(child, depth + 1));
      continue;
    }
    const content = serializeBlock(child, depth).trim();
    if (content) blocks.push(content);
  }

  const head = `${indent}${marker}${blocks.join(' ').trim() || ' '}`.trimEnd();
  return [head, ...nested.filter(Boolean)].join('\n');
}

function serializeList(node: SerializedNode, depth = 0): string {
  const ordered = node.type === 'list' && node.listType === 'number';
  return (node.children ?? [])
    .filter((child) => child.type === 'listitem')
    .map((child, index) => serializeListItem(child, ordered, depth, index))
    .join('\n');
}

function serializeTable(node: SerializedNode): string {
  const rows = (node.children ?? []).map((row) =>
    (row.children ?? []).map((cell) =>
      (cell.children ?? [])
        .map(serializeParagraph)
        .filter(Boolean)
        .join('<br>')
        .replace(/\|/g, '\\|')
    )
  );

  if (rows.length === 0) return '';
  const headers = rows[0];
  const separator = headers.map(() => '---');
  const body = rows.slice(1);
  return [
    `| ${headers.join(' | ')} |`,
    `| ${separator.join(' | ')} |`,
    ...body.map((row) => `| ${row.join(' | ')} |`),
  ].join('\n');
}

function serializeBlock(node: SerializedNode, depth = 0): string {
  switch (node.type) {
    case 'heading': {
      const level = Number((node.tag ?? 'h1').replace('h', '')) || 1;
      return `${'#'.repeat(Math.min(Math.max(level, 1), 6))} ${serializeInlineChildren(node).trim()}`.trim();
    }
    case 'quote': {
      const content = serializeInlineChildren(node).trim();
      return content
        .split('\n')
        .filter(Boolean)
        .map((line) => `> ${line}`)
        .join('\n');
    }
    case 'list':
      return serializeList(node, depth);
    case 'paragraph':
      return serializeParagraph(node);
    case 'code-block':
    case 'snippet': {
      const title = node.caption ? `> ${node.caption}\n` : '';
      const language = node.language ?? '';
      return `${title}\`\`\`${language}\n${node.code ?? ''}\n\`\`\``;
    }
    case 'lecture-image': {
      const image = `![${node.altText ?? ''}](${node.src ?? ''})`;
      return node.caption ? `${image}\n\n_${node.caption}_` : image;
    }
    case 'math':
      return node.displayMode ? `$$\n${node.latex ?? ''}\n$$` : `$${node.latex ?? ''}$`;
    case 'table':
      return serializeTable(node);
    default:
      return serializeInline(node).trim();
  }
}

export function lexicalToMarkdown(state?: SerializedEditorState | null): string {
  const root = state?.root as SerializedNode | undefined;
  const blocks = (root?.children ?? []).map((node) => serializeBlock(node)).filter(Boolean);
  return blocks.join('\n\n').trim();
}

export function downloadMarkdownFile(filename: string, content: string): void {
  const safeName = filename.trim().replace(/[\\/:*?"<>|]+/g, '_') || 'lecture';
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = safeName.endsWith('.md') ? safeName : `${safeName}.md`;
  link.click();
  URL.revokeObjectURL(url);
}
