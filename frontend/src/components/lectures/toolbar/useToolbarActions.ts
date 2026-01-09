'use client';

import { useCallback } from 'react';
import { LexicalEditor } from 'lexical';
import { 
  $getSelection, 
  $isRangeSelection,
  FORMAT_TEXT_COMMAND,
  FORMAT_ELEMENT_COMMAND,
  UNDO_COMMAND,
  REDO_COMMAND,
  INDENT_CONTENT_COMMAND,
  OUTDENT_CONTENT_COMMAND,
  $getRoot,
  ElementFormatType,
} from 'lexical';
import { $setBlocksType, $patchStyleText } from '@lexical/selection';
import { $createHeadingNode, $createQuoteNode, HeadingTagType } from '@lexical/rich-text';
import { INSERT_ORDERED_LIST_COMMAND, INSERT_UNORDERED_LIST_COMMAND } from '@lexical/list';
import { toast } from 'sonner';
import { $createCodeBlockNode } from '../nodes/CodeBlockNode';
import { $createImageNode } from '../nodes/ImageNode';
import { INSERT_HORIZONTAL_RULE_COMMAND } from '../nodes/HorizontalRuleNode';

export function useToolbarActions(editor: LexicalEditor) {
  // Text formatting
  const formatBold = useCallback(() => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'bold');
  }, [editor]);

  const formatItalic = useCallback(() => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'italic');
  }, [editor]);

  const formatUnderline = useCallback(() => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'underline');
  }, [editor]);

  const formatStrikethrough = useCallback(() => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'strikethrough');
  }, [editor]);

  const formatCode = useCallback(() => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'code');
  }, [editor]);

  const formatSubscript = useCallback(() => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'subscript');
  }, [editor]);

  const formatSuperscript = useCallback(() => {
    editor.dispatchCommand(FORMAT_TEXT_COMMAND, 'superscript');
  }, [editor]);

  // Block formatting
  const formatHeading = useCallback((tag: HeadingTagType) => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        $setBlocksType(selection, () => $createHeadingNode(tag));
      }
    });
  }, [editor]);

  const formatQuote = useCallback(() => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        $setBlocksType(selection, () => $createQuoteNode());
      }
    });
  }, [editor]);

  // Lists
  const formatBulletList = useCallback(() => {
    editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined);
  }, [editor]);

  const formatNumberedList = useCallback(() => {
    editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined);
  }, [editor]);

  // Insert blocks
  const insertCodeBlock = useCallback(() => {
    editor.update(() => {
      const selection = $getSelection();
      const codeBlock = $createCodeBlockNode('// Введите код здесь...', 'javascript', 'code');
      if ($isRangeSelection(selection)) {
        selection.insertNodes([codeBlock]);
      } else {
        $getRoot().append(codeBlock);
      }
      toast.success('Блок кода добавлен');
    });
  }, [editor]);

  const insertImage = useCallback(() => {
    editor.update(() => {
      const selection = $getSelection();
      const imageNode = $createImageNode('', 'Изображение', '', 'auto', 'auto');
      if ($isRangeSelection(selection)) {
        selection.insertNodes([imageNode]);
      } else {
        $getRoot().append(imageNode);
      }
      toast.success('Блок изображения добавлен');
    });
  }, [editor]);

  const insertHorizontalRule = useCallback(() => {
    editor.dispatchCommand(INSERT_HORIZONTAL_RULE_COMMAND, undefined);
    toast.success('Разделитель добавлен');
  }, [editor]);

  const insertSnippet = useCallback(() => {
    editor.update(() => {
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      const { $createSnippetNode } = require('../nodes/SnippetNode');
      const selection = $getSelection();
      const snippetNode = $createSnippetNode('// Пример кода', 'javascript', '', true);
      if ($isRangeSelection(selection)) {
        selection.insertNodes([snippetNode]);
      } else {
        $getRoot().append(snippetNode);
      }
      toast.success('Листинг добавлен');
    });
  }, [editor]);

  // History
  const undo = useCallback(() => {
    editor.dispatchCommand(UNDO_COMMAND, undefined);
  }, [editor]);

  const redo = useCallback(() => {
    editor.dispatchCommand(REDO_COMMAND, undefined);
  }, [editor]);

  // Text alignment
  const formatAlign = useCallback((alignment: ElementFormatType) => {
    editor.dispatchCommand(FORMAT_ELEMENT_COMMAND, alignment);
  }, [editor]);

  // Indent/Outdent
  const indent = useCallback(() => {
    editor.dispatchCommand(INDENT_CONTENT_COMMAND, undefined);
  }, [editor]);

  const outdent = useCallback(() => {
    editor.dispatchCommand(OUTDENT_CONTENT_COMMAND, undefined);
  }, [editor]);

  // Font size
  const applyFontSize = useCallback((size: string) => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        $patchStyleText(selection, {
          'font-size': size === '16' ? null : `${size}px`,
        });
      }
    });
  }, [editor]);

  // Line height
  const applyLineHeight = useCallback((height: string) => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        $patchStyleText(selection, {
          'line-height': height === '1.5' ? null : height,
        });
      }
    });
  }, [editor]);

  return {
    formatBold,
    formatItalic,
    formatUnderline,
    formatStrikethrough,
    formatCode,
    formatSubscript,
    formatSuperscript,
    formatHeading,
    formatQuote,
    formatBulletList,
    formatNumberedList,
    insertCodeBlock,
    insertImage,
    insertHorizontalRule,
    insertSnippet,
    undo,
    redo,
    formatAlign,
    indent,
    outdent,
    applyFontSize,
    applyLineHeight,
  };
}
