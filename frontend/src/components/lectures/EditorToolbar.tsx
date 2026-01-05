'use client';

import { useCallback } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { 
  $getSelection, 
  $isRangeSelection,
  FORMAT_TEXT_COMMAND,
  FORMAT_ELEMENT_COMMAND,
  $createParagraphNode,
  UNDO_COMMAND,
  REDO_COMMAND,
  INDENT_CONTENT_COMMAND,
  OUTDENT_CONTENT_COMMAND,
  $getRoot,
  ElementFormatType,
} from 'lexical';
import { $setBlocksType, $patchStyleText } from '@lexical/selection';
import { $createHeadingNode, $createQuoteNode, HeadingTagType } from '@lexical/rich-text';
import { 
  INSERT_ORDERED_LIST_COMMAND, 
  INSERT_UNORDERED_LIST_COMMAND,
} from '@lexical/list';
import { Button } from '@/components/ui/button';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipTrigger 
} from '@/components/ui/tooltip';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import {
  Bold,
  Italic,
  Underline,
  Strikethrough,
  Code,
  Heading1,
  Heading2,
  Heading3,
  List,
  ListOrdered,
  Quote,
  Image,
  FileCode,
  FileCode2,
  Undo,
  Redo,
  Save,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  IndentIncrease,
  IndentDecrease,
  Subscript,
  Superscript,
  Minus,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import { $createCodeBlockNode } from './nodes/CodeBlockNode';
import { $createImageNode } from './nodes/ImageNode';
import { INSERT_HORIZONTAL_RULE_COMMAND } from './nodes/HorizontalRuleNode';

const FONT_SIZES = ['12', '14', '16', '18', '20', '24', '28', '32'] as const;
const LINE_HEIGHTS = ['1', '1.15', '1.5', '2'] as const;

interface EditorToolbarProps {
  onSave?: () => void;
  isSaving?: boolean;
  className?: string;
}

interface ToolbarButtonProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  isActive?: boolean;
  disabled?: boolean;
}

function ToolbarButton({ icon, label, onClick, isActive, disabled }: ToolbarButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "h-8 w-8 p-0",
            isActive && "bg-accent text-accent-foreground"
          )}
          onClick={onClick}
          disabled={disabled}
        >
          {icon}
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        <p>{label}</p>
      </TooltipContent>
    </Tooltip>
  );
}

// Группа кнопок с подписью
function ToolbarGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <div className="flex items-center gap-0.5">
        {children}
      </div>
      <span className="text-[10px] text-muted-foreground/60 select-none">{label}</span>
    </div>
  );
}

export function EditorToolbar({ onSave, isSaving, className }: EditorToolbarProps) {
  const [editor] = useLexicalComposerContext();

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
      if ($isRangeSelection(selection)) {
        const codeBlock = $createCodeBlockNode('// Введите код здесь...', 'javascript', 'code');
        selection.insertNodes([codeBlock]);
        toast.success('Блок кода добавлен');
      } else {
        const root = $getRoot();
        const codeBlock = $createCodeBlockNode('// Введите код здесь...', 'javascript', 'code');
        root.append(codeBlock);
        toast.success('Блок кода добавлен');
      }
    });
  }, [editor]);

  const insertImage = useCallback(() => {
    editor.update(() => {
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        const imageNode = $createImageNode('', 'Изображение', '', 'auto', 'auto');
        selection.insertNodes([imageNode]);
        toast.success('Блок изображения добавлен');
      } else {
        const root = $getRoot();
        const imageNode = $createImageNode('', 'Изображение', '', 'auto', 'auto');
        root.append(imageNode);
        toast.success('Блок изображения добавлен');
      }
    });
  }, [editor]);

  const insertHorizontalRule = useCallback(() => {
    editor.dispatchCommand(INSERT_HORIZONTAL_RULE_COMMAND, undefined);
    toast.success('Разделитель добавлен');
  }, [editor]);

  const insertSnippet = useCallback(() => {
    editor.update(() => {
      const { $createSnippetNode } = require('./nodes/SnippetNode');
      const selection = $getSelection();
      if ($isRangeSelection(selection)) {
        const snippetNode = $createSnippetNode('// Пример кода', 'javascript', '', true);
        selection.insertNodes([snippetNode]);
        toast.success('Листинг добавлен');
      } else {
        const root = $getRoot();
        const snippetNode = $createSnippetNode('// Пример кода', 'javascript', '', true);
        root.append(snippetNode);
        toast.success('Листинг добавлен');
      }
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

  return (
    <div className={cn(
      "flex flex-wrap items-end gap-3 p-3 border-b bg-muted/40",
      className
    )}>
      {/* История */}
      <ToolbarGroup label="История">
        <ToolbarButton icon={<Undo className="h-4 w-4" />} label="Отменить (Ctrl+Z)" onClick={undo} />
        <ToolbarButton icon={<Redo className="h-4 w-4" />} label="Повторить (Ctrl+Y)" onClick={redo} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Форматирование текста */}
      <ToolbarGroup label="Текст">
        <ToolbarButton icon={<Bold className="h-4 w-4" />} label="Жирный (Ctrl+B)" onClick={formatBold} />
        <ToolbarButton icon={<Italic className="h-4 w-4" />} label="Курсив (Ctrl+I)" onClick={formatItalic} />
        <ToolbarButton icon={<Underline className="h-4 w-4" />} label="Подчёркнутый (Ctrl+U)" onClick={formatUnderline} />
        <ToolbarButton icon={<Strikethrough className="h-4 w-4" />} label="Зачёркнутый" onClick={formatStrikethrough} />
        <ToolbarButton icon={<Code className="h-4 w-4" />} label="Код" onClick={formatCode} />
        <ToolbarButton icon={<Subscript className="h-4 w-4" />} label="Подстрочный" onClick={formatSubscript} />
        <ToolbarButton icon={<Superscript className="h-4 w-4" />} label="Надстрочный" onClick={formatSuperscript} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Заголовки */}
      <ToolbarGroup label="Заголовки">
        <ToolbarButton icon={<Heading1 className="h-4 w-4" />} label="Заголовок 1" onClick={() => formatHeading('h1')} />
        <ToolbarButton icon={<Heading2 className="h-4 w-4" />} label="Заголовок 2" onClick={() => formatHeading('h2')} />
        <ToolbarButton icon={<Heading3 className="h-4 w-4" />} label="Заголовок 3" onClick={() => formatHeading('h3')} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Списки */}
      <ToolbarGroup label="Списки">
        <ToolbarButton icon={<List className="h-4 w-4" />} label="Маркированный" onClick={formatBulletList} />
        <ToolbarButton icon={<ListOrdered className="h-4 w-4" />} label="Нумерованный" onClick={formatNumberedList} />
        <ToolbarButton icon={<Quote className="h-4 w-4" />} label="Цитата" onClick={formatQuote} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Выравнивание */}
      <ToolbarGroup label="Выравнивание">
        <ToolbarButton icon={<AlignLeft className="h-4 w-4" />} label="По левому краю" onClick={() => formatAlign('left')} />
        <ToolbarButton icon={<AlignCenter className="h-4 w-4" />} label="По центру" onClick={() => formatAlign('center')} />
        <ToolbarButton icon={<AlignRight className="h-4 w-4" />} label="По правому краю" onClick={() => formatAlign('right')} />
        <ToolbarButton icon={<AlignJustify className="h-4 w-4" />} label="По ширине" onClick={() => formatAlign('justify')} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Отступы */}
      <ToolbarGroup label="Отступы">
        <ToolbarButton icon={<IndentDecrease className="h-4 w-4" />} label="Уменьшить" onClick={outdent} />
        <ToolbarButton icon={<IndentIncrease className="h-4 w-4" />} label="Увеличить" onClick={indent} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Размер и интервал */}
      <ToolbarGroup label="Шрифт">
        <Select onValueChange={applyFontSize} defaultValue="16">
          <SelectTrigger className="h-8 w-[65px] text-xs">
            <SelectValue placeholder="16" />
          </SelectTrigger>
          <SelectContent>
            {FONT_SIZES.map((size) => (
              <SelectItem key={size} value={size} className="text-xs">
                {size}px
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select onValueChange={applyLineHeight} defaultValue="1.5">
          <SelectTrigger className="h-8 w-[60px] text-xs">
            <SelectValue placeholder="1.5" />
          </SelectTrigger>
          <SelectContent>
            {LINE_HEIGHTS.map((height) => (
              <SelectItem key={height} value={height} className="text-xs">
                ×{height}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Вставка */}
      <ToolbarGroup label="Вставка">
        <ToolbarButton icon={<FileCode className="h-4 w-4" />} label="Блок кода (визуализация)" onClick={insertCodeBlock} />
        <ToolbarButton icon={<FileCode2 className="h-4 w-4" />} label="Листинг (пример кода)" onClick={insertSnippet} />
        <ToolbarButton icon={<Image className="h-4 w-4" />} label="Изображение" onClick={insertImage} />
        <ToolbarButton icon={<Minus className="h-4 w-4" />} label="Разделитель (---)" onClick={insertHorizontalRule} />
      </ToolbarGroup>
      
      {/* Сохранить */}
      {onSave && (
        <>
          <div className="flex-1" />
          <Button
            variant="default"
            size="sm"
            onClick={onSave}
            disabled={isSaving}
            className="gap-1.5 h-9"
          >
            <Save className="h-4 w-4" />
            {isSaving ? 'Сохранение...' : 'Сохранить'}
          </Button>
        </>
      )}
    </div>
  );
}

export default EditorToolbar;
