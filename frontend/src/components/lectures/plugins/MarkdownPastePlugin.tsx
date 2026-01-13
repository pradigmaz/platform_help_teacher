'use client';

import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getRoot, $getSelection, $isRangeSelection, $createParagraphNode, PASTE_COMMAND, COMMAND_PRIORITY_HIGH } from 'lexical';
import { $createCodeBlockNode, type CodeLanguage } from '../nodes/CodeBlockNode';
import { $createImageNode } from '../nodes/ImageNode';
import { $createTableFromMarkdown } from './markdown/table-parser';
import { $parseMarkdownLine } from './markdown/block-parser';
import { extractCustomBlocks, splitByPlaceholders, type CodeBlockData, type ImageData } from './markdown/placeholder-processor';
import type { MarkdownTableData } from './markdown/table-parser';

export function MarkdownPastePlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand(
      PASTE_COMMAND,
      (event: ClipboardEvent) => {
        const text = event.clipboardData?.getData('text/plain');
        if (!text) return false;
        
        // Check if it looks like markdown
        const hasMarkdown = /^#{1,6}\s|^```|^!\[|^>\s|^[-*]\s|^\d+\.\s|\*\*|__|\*[^*]|_[^_]|^\|.+\|$/m.test(text);
        if (!hasMarkdown) return false;
        
        event.preventDefault();
        
        // Normalize line endings
        const normalizedText = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        
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
              // Parse markdown lines
              const lines = part.split('\n');
              for (const line of lines) {
                const node = $parseMarkdownLine(line);
                if (node) nodesToInsert.push(node);
              }
            }
          }
          
          // Insert nodes
          if ($isRangeSelection(selection) && nodesToInsert.length > 0) {
            selection.removeText();
            for (const node of nodesToInsert) {
              selection.insertNodes([node]);
            }
          } else {
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
