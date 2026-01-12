'use client';

import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getRoot,
  $getSelection,
  $isRangeSelection,
  $createParagraphNode,
  $createTextNode,
  PASTE_COMMAND,
  COMMAND_PRIORITY_HIGH,
} from 'lexical';
import { $convertFromMarkdownString } from '@lexical/markdown';
import { 
  BOLD_ITALIC_STAR, 
  BOLD_ITALIC_UNDERSCORE, 
  BOLD_STAR, 
  BOLD_UNDERSCORE, 
  ITALIC_STAR, 
  ITALIC_UNDERSCORE, 
  STRIKETHROUGH,
  HEADING,
  QUOTE,
  UNORDERED_LIST,
  ORDERED_LIST,
} from '@lexical/markdown';
import { 
  $createTableNode, 
  $createTableRowNode, 
  $createTableCellNode,
  TableCellHeaderStates,
} from '@lexical/table';
import { $createCodeBlockNode, type CodeLanguage } from '../nodes/CodeBlockNode';
import { $createImageNode } from '../nodes/ImageNode';

// Transformers without CodeNode dependency
const LECTURE_TRANSFORMERS = [
  HEADING,
  QUOTE,
  UNORDERED_LIST,
  ORDERED_LIST,
  BOLD_ITALIC_STAR,
  BOLD_ITALIC_UNDERSCORE,
  BOLD_STAR,
  BOLD_UNDERSCORE,
  ITALIC_STAR,
  ITALIC_UNDERSCORE,
  STRIKETHROUGH,
];

// Parse markdown table into structured data
function parseMarkdownTable(tableText: string): { headers: string[]; rows: string[][] } | null {
  const lines = tableText.trim().split('\n').filter(line => line.trim());
  if (lines.length < 2) return null;
  
  const parseRow = (line: string): string[] => {
    return line
      .split('|')
      .map(cell => cell.trim())
      .filter((_, i, arr) => i > 0 && i < arr.length - 1 || (arr.length === 1 && arr[0]));
  };
  
  const headers = parseRow(lines[0]);
  if (headers.length === 0) return null;
  
  // Check if second line is separator (---|---|---)
  const separatorLine = lines[1];
  if (!/^[\s|:-]+$/.test(separatorLine)) return null;
  
  const rows: string[][] = [];
  for (let i = 2; i < lines.length; i++) {
    const row = parseRow(lines[i]);
    if (row.length > 0) {
      // Pad row to match header length
      while (row.length < headers.length) row.push('');
      rows.push(row.slice(0, headers.length));
    }
  }
  
  return { headers, rows };
}

// Create Lexical table node from parsed data
function $createTableFromMarkdown(data: { headers: string[]; rows: string[][] }) {
  const tableNode = $createTableNode();
  
  // Header row
  const headerRow = $createTableRowNode();
  for (const header of data.headers) {
    const cell = $createTableCellNode(TableCellHeaderStates.ROW);
    const paragraph = $createParagraphNode();
    paragraph.append($createTextNode(header));
    cell.append(paragraph);
    headerRow.append(cell);
  }
  tableNode.append(headerRow);
  
  // Data rows
  for (const row of data.rows) {
    const tableRow = $createTableRowNode();
    for (const cellText of row) {
      const cell = $createTableCellNode(TableCellHeaderStates.NO_STATUS);
      const paragraph = $createParagraphNode();
      paragraph.append($createTextNode(cellText));
      cell.append(paragraph);
      tableRow.append(cell);
    }
    tableNode.append(tableRow);
  }
  
  return tableNode;
}

export function MarkdownPastePlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand(
      PASTE_COMMAND,
      (event: ClipboardEvent) => {
        const text = event.clipboardData?.getData('text/plain');
        if (!text) return false;
        
        // Check if it looks like markdown (including tables with |)
        const hasMarkdown = /^#\s|^```|^!\[|^>\s|^[-*]\s|^\d+\.\s|\*\*|__|\*[^*]|_[^_]|^\|.+\|$/m.test(text);
        if (!hasMarkdown) return false;
        
        event.preventDefault();
        
        // Normalize line endings
        const normalizedText = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        
        // Extract code blocks, images, and tables first (custom nodes)
        const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
        const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
        // Table: lines starting and ending with |, at least 2 lines with separator
        const tableRegex = /(?:^\|.+\|[ \t]*\n?)+/gm;
        
        // Store custom blocks with placeholders
        const customBlocks: Array<{ type: 'code' | 'image' | 'table'; data: unknown; placeholder: string }> = [];
        let processedText = normalizedText;
        let placeholderIndex = 0;
        
        // Replace code blocks with placeholders
        processedText = processedText.replace(codeBlockRegex, (match, lang, code) => {
          const placeholder = `__CODE_BLOCK_${placeholderIndex}__`;
          customBlocks.push({
            type: 'code',
            data: { language: lang || 'javascript', code: code.trim() },
            placeholder,
          });
          placeholderIndex++;
          return placeholder;
        });
        
        // Replace tables with placeholders
        processedText = processedText.replace(tableRegex, (match) => {
          const tableData = parseMarkdownTable(match);
          if (tableData) {
            const placeholder = `__TABLE_${placeholderIndex}__`;
            customBlocks.push({
              type: 'table',
              data: tableData,
              placeholder,
            });
            placeholderIndex++;
            return placeholder;
          }
          return match; // Keep original if not valid table
        });
        
        // Replace images with placeholders
        processedText = processedText.replace(imageRegex, (match, alt, src) => {
          const placeholder = `__IMAGE_${placeholderIndex}__`;
          customBlocks.push({
            type: 'image',
            data: { alt, src },
            placeholder,
          });
          placeholderIndex++;
          return placeholder;
        });
        
        editor.update(() => {
          const root = $getRoot();
          const selection = $getSelection();
          
          // Создаём ноды из markdown
          const tempRoot = $getRoot();
          const insertionPoint = $isRangeSelection(selection) ? selection.anchor.getNode() : null;
          
          // Парсим markdown во временные ноды
          const nodesToInsert: import('lexical').LexicalNode[] = [];
          
          // Разбиваем текст на части по плейсхолдерам и обычный текст
          const parts = processedText.split(/(__(?:CODE_BLOCK|TABLE|IMAGE)_\d+__)/);
          
          for (const part of parts) {
            if (!part.trim()) continue;
            
            // Проверяем, это плейсхолдер или обычный текст
            const block = customBlocks.find(b => b.placeholder === part);
            
            if (block) {
              if (block.type === 'code') {
                const { language, code } = block.data as { language: string; code: string };
                nodesToInsert.push($createCodeBlockNode(code, language as CodeLanguage, 'code'));
              } else if (block.type === 'image') {
                const { alt, src } = block.data as { alt: string; src: string };
                nodesToInsert.push($createImageNode(src, alt, '', 'auto', 'auto'));
              } else if (block.type === 'table') {
                const tableData = block.data as { headers: string[]; rows: string[][] };
                nodesToInsert.push($createTableFromMarkdown(tableData));
              }
            } else {
              // Обычный markdown текст — конвертируем построчно
              const lines = part.split('\n');
              for (const line of lines) {
                if (!line.trim()) continue;
                const paragraph = $createParagraphNode();
                paragraph.append($createTextNode(line));
                nodesToInsert.push(paragraph);
              }
            }
          }
          
          // Вставляем ноды в позицию курсора
          if ($isRangeSelection(selection) && nodesToInsert.length > 0) {
            // Удаляем выделенный текст если есть
            selection.removeText();
            
            // Вставляем все ноды
            for (const node of nodesToInsert) {
              selection.insertNodes([node]);
            }
          } else {
            // Если нет selection, добавляем в конец
            for (const node of nodesToInsert) {
              root.append(node);
            }
          }
          
          // Ensure at least one paragraph
          if (root.getChildrenSize() === 0) {
            root.append($createParagraphNode());
          }
        });
        
        return true;
      },
      COMMAND_PRIORITY_HIGH
    );
  }, [editor]);

  return null;
}

export default MarkdownPastePlugin;
