import { parseMarkdownTable, type MarkdownTableData } from './table-parser';
import { $createMathNode } from '../../nodes/MathNode';

export type CustomBlockType = 'code' | 'image' | 'table' | 'math';

export interface CustomBlock {
  type: CustomBlockType;
  data: unknown;
  placeholder: string;
}

export interface CodeBlockData {
  language: string;
  code: string;
}

export interface ImageData {
  alt: string;
  src: string;
}

export interface MathBlockData {
  latex: string;
}

/**
 * Извлекает code blocks, images, tables, math blocks и заменяет их плейсхолдерами
 */
export function extractCustomBlocks(text: string): { processedText: string; blocks: CustomBlock[] } {
  const customBlocks: CustomBlock[] = [];
  let processedText = text;
  let placeholderIndex = 0;
  
  // Extract display math blocks: \[...\] or $$...$$
  const displayMathRegex = /\\\[([\s\S]*?)\\\]|\$\$([\s\S]*?)\$\$/g;
  processedText = processedText.replace(displayMathRegex, (_match, latex1, latex2) => {
    const latex = (latex1 || latex2 || '').trim();
    const placeholder = `__MATH_BLOCK_${placeholderIndex}__`;
    customBlocks.push({
      type: 'math',
      data: { latex } as MathBlockData,
      placeholder,
    });
    placeholderIndex++;
    return placeholder;
  });
  
  // Extract code blocks
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
  processedText = processedText.replace(codeBlockRegex, (_match, lang, code) => {
    const placeholder = `__CODE_BLOCK_${placeholderIndex}__`;
    customBlocks.push({
      type: 'code',
      data: { language: lang || 'javascript', code: code.trim() } as CodeBlockData,
      placeholder,
    });
    placeholderIndex++;
    return placeholder;
  });
  
  // Extract tables
  const tableRegex = /(?:^\|.+\|[ \t]*\n?)+/gm;
  processedText = processedText.replace(tableRegex, (match) => {
    const tableData = parseMarkdownTable(match);
    if (tableData) {
      const placeholder = `__TABLE_${placeholderIndex}__`;
      customBlocks.push({
        type: 'table',
        data: tableData as MarkdownTableData,
        placeholder,
      });
      placeholderIndex++;
      return placeholder;
    }
    return match;
  });
  
  // Extract images
  const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
  processedText = processedText.replace(imageRegex, (_match, alt, src) => {
    const placeholder = `__IMAGE_${placeholderIndex}__`;
    customBlocks.push({
      type: 'image',
      data: { alt, src } as ImageData,
      placeholder,
    });
    placeholderIndex++;
    return placeholder;
  });
  
  return { processedText, blocks: customBlocks };
}

/**
 * Разбивает текст на части: плейсхолдеры и обычный текст
 */
export function splitByPlaceholders(text: string): string[] {
  return text.split(/(__(?:CODE_BLOCK|TABLE|IMAGE|MATH_BLOCK)_\d+__)/);
}

export { $createMathNode };
