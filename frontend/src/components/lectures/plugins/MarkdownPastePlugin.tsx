'use client';

import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getRoot, $getSelection, $isRangeSelection, $createParagraphNode, PASTE_COMMAND, COMMAND_PRIORITY_CRITICAL } from 'lexical';
import { $createCodeBlockNode, type CodeLanguage } from '../nodes/CodeBlockNode';
import { $createImageNode } from '../nodes/ImageNode';
import { $createTableFromMarkdown } from './markdown/table-parser';
import { $parseMarkdownLines } from './markdown/block-parser';
import { extractCustomBlocks, splitByPlaceholders, type CodeBlockData, type ImageData } from './markdown/placeholder-processor';
import type { MarkdownTableData } from './markdown/table-parser';

/**
 * Проверяет, содержит ли текст markdown-разметку
 */
function detectMarkdown(text: string): boolean {
  // Заголовки: ## Text
  if (/^#{1,6}\s+.+$/m.test(text)) return true;
  // Код: ```
  if (/^```/m.test(text)) return true;
  // Изображения: ![alt](src)
  if (/!\[.*?\]\(.*?\)/.test(text)) return true;
  // Цитаты: > text
  if (/^>\s+.+$/m.test(text)) return true;
  // Маркированные списки: - item или * item
  if (/^[-*]\s+.+$/m.test(text)) return true;
  // Нумерованные списки: 1. item
  if (/^\d+\.\s+.+$/m.test(text)) return true;
  // Жирный: **text** или __text__
  if (/\*\*[^*]+\*\*/.test(text)) return true;
  if (/__[^_]+__/.test(text)) return true;
  // Курсив: *text* или _text_ (не внутри слов)
  if (/(?<!\w)\*[^*\s][^*]*[^*\s]\*(?!\w)/.test(text)) return true;
  // Таблицы: |...|
  if (/^\|.+\|$/m.test(text)) return true;
  
  return false;
}

export function MarkdownPastePlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand(
      PASTE_COMMAND,
      (event: ClipboardEvent) => {
        // Получаем plain text — игнорируем HTML версию
        const text = event.clipboardData?.getData('text/plain');
        if (!text) return false;
        
        // Проверяем наличие markdown
        const hasMarkdown = detectMarkdown(text);
        const newlineCount = (text.match(/\n/g) || []).length;
        console.log('[MarkdownPaste] hasMarkdown:', hasMarkdown, 'length:', text.length, 'newlines:', newlineCount);
        console.log('[MarkdownPaste] First 200 chars:', JSON.stringify(text.slice(0, 200)));
        
        if (!hasMarkdown) {
          console.log('[MarkdownPaste] No markdown detected, passing to default handler');
          return false;
        }
        
        // Предотвращаем стандартную обработку
        event.preventDefault();
        console.log('[MarkdownPaste] Processing markdown paste...');
        
        // Normalize line endings
        let normalizedText = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        
        // Если переносов строк мало, но есть markdown-паттерны подряд — 
        // вероятно переносы потерялись при копировании
        const newlineCount = (normalizedText.match(/\n/g) || []).length;
        const headingCount = (normalizedText.match(/#{1,6}\s/g) || []).length;
        
        console.log('[MarkdownPaste] newlines:', newlineCount, 'headings:', headingCount);
        
        // Если заголовков больше чем переносов — переносы потерялись
        if (headingCount > 1 && newlineCount < headingCount) {
          console.log('[MarkdownPaste] Detected lost newlines, restoring...');
          // Восстанавливаем переносы перед заголовками
          normalizedText = normalizedText
            .replace(/([^\n])(#{1,6}\s)/g, '$1\n\n$2')
            // Перед жирным текстом в начале "предложения" (после точки)
            .replace(/\.(\*\*[А-ЯA-Z])/g, '.\n\n$1')
            // Перед списками
            .replace(/([^\n])(\n?[-*]\s)/g, '$1\n$2')
            .replace(/([^\n])(\n?\d+\.\s)/g, '$1\n$2');
        }
        
        // Extract custom blocks (code, images, tables)
        const { processedText, blocks } = extractCustomBlocks(normalizedText);
        
        editor.update(() => {
          const root = $getRoot();
          const selection = $getSelection();
          const nodesToInsert: import('lexical').LexicalNode[] = [];
          
          // Split by placeholders
          const parts = splitByPlaceholders(processedText);
          
          for (const part of parts) {
            if (!part.trim()) continue;
            
            // Check if placeholder
            const block = blocks.find(b => b.placeholder === part);
            
            if (block) {
              console.log('[MarkdownPaste] Found block:', block.type);
              if (block.type === 'code') {
                const { language, code } = block.data as CodeBlockData;
                nodesToInsert.push($createCodeBlockNode(code, language as CodeLanguage, 'code'));
              } else if (block.type === 'image') {
                const { alt, src } = block.data as ImageData;
                nodesToInsert.push($createImageNode(src, alt, '', 'auto', 'auto'));
              } else if (block.type === 'table') {
                const tableData = block.data as MarkdownTableData;
                nodesToInsert.push($createTableFromMarkdown(tableData));
              }
            } else {
              // Parse markdown lines with proper list grouping
              const lines = part.split('\n');
              console.log('[MarkdownPaste] Parsing', lines.length, 'lines');
              const parsedNodes = $parseMarkdownLines(lines);
              console.log('[MarkdownPaste] Created', parsedNodes.length, 'nodes');
              nodesToInsert.push(...parsedNodes);
            }
          }
          
          // Insert nodes
          console.log('[MarkdownPaste] Total nodes to insert:', nodesToInsert.length);
          if ($isRangeSelection(selection) && nodesToInsert.length > 0) {
            selection.removeText();
            for (const node of nodesToInsert) {
              selection.insertNodes([node]);
            }
          } else {
            // Clear root and add new nodes
            root.clear();
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
      COMMAND_PRIORITY_CRITICAL // Максимальный приоритет
    );
  }, [editor]);

  return null;
}

export default MarkdownPastePlugin;
