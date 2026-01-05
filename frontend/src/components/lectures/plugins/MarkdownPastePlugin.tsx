'use client';

import { useEffect } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getRoot,
  $getSelection,
  $isRangeSelection,
  $createParagraphNode,
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

export function MarkdownPastePlugin(): null {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    return editor.registerCommand(
      PASTE_COMMAND,
      (event: ClipboardEvent) => {
        const text = event.clipboardData?.getData('text/plain');
        if (!text) return false;
        
        // Check if it looks like markdown
        const hasMarkdown = /^#\s|^```|^!\[|^>\s|^[-*]\s|^\d+\.\s|\*\*|__|\*[^*]|_[^_]/m.test(text);
        if (!hasMarkdown) return false;
        
        event.preventDefault();
        
        // Normalize line endings
        const normalizedText = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        
        // Extract code blocks and images first (custom nodes)
        const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
        const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
        
        // Store custom blocks with placeholders
        const customBlocks: Array<{ type: 'code' | 'image'; data: unknown; placeholder: string }> = [];
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
          
          // Clear if pasting at root level
          if ($isRangeSelection(selection)) {
            root.clear();
          }
          
          // Use Lexical's markdown converter for text formatting
          $convertFromMarkdownString(processedText, LECTURE_TRANSFORMERS);
          
          // Now replace placeholders with custom nodes
          const children = root.getChildren();
          for (const child of children) {
            const textContent = child.getTextContent();
            
            for (const block of customBlocks) {
              if (textContent.includes(block.placeholder)) {
                // Create custom node
                if (block.type === 'code') {
                  const { language, code } = block.data as { language: string; code: string };
                  const codeNode = $createCodeBlockNode(code, language as CodeLanguage, 'code');
                  child.insertBefore(codeNode);
                  child.remove();
                } else if (block.type === 'image') {
                  const { alt, src } = block.data as { alt: string; src: string };
                  const imageNode = $createImageNode(src, alt, '', 'auto', 'auto');
                  child.insertBefore(imageNode);
                  child.remove();
                }
                break;
              }
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
