'use client';

import React from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import {
  Bold, Italic, Underline, Strikethrough, Code,
  Heading1, Heading2, Heading3, List, ListOrdered, Quote,
  Image, FileCode, FileCode2, Undo, Redo, Save,
  AlignLeft, AlignCenter, AlignRight, AlignJustify,
  IndentIncrease, IndentDecrease, Subscript, Superscript, Minus,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ToolbarButton, ToolbarGroup, useToolbarActions, FONT_SIZES, LINE_HEIGHTS } from './toolbar';
import { PresetConfig } from './presets';

interface EditorToolbarProps {
  onSave?: () => void;
  isSaving?: boolean;
  className?: string;
  config?: PresetConfig;
  onFontSizeChange?: (size: string) => void;
  onLineHeightChange?: (height: string) => void;
}

export function EditorToolbar({ onSave, isSaving, className, config, onFontSizeChange, onLineHeightChange }: EditorToolbarProps) {
  const [editor] = useLexicalComposerContext();
  const actions = useToolbarActions(editor);

  // Дефолт — всё включено
  const c = config ?? {
    showHistory: true, showTextFormat: true, showHeadings: true,
    showLists: true, showAlign: true, showIndent: true,
    showFontSize: true, showInsert: true, showSave: true,
    minHeight: '400px', padding: 'px-4 py-4',
  };

  const groups: React.ReactNode[] = [];

  if (c.showHistory) {
    groups.push(
      <ToolbarGroup key="history" label="История">
        <ToolbarButton icon={<Undo className="h-4 w-4" />} label="Отменить" onClick={actions.undo} />
        <ToolbarButton icon={<Redo className="h-4 w-4" />} label="Повторить" onClick={actions.redo} />
      </ToolbarGroup>
    );
  }

  if (c.showTextFormat) {
    groups.push(
      <ToolbarGroup key="text" label="Текст">
        <ToolbarButton icon={<Bold className="h-4 w-4" />} label="Жирный" onClick={actions.formatBold} />
        <ToolbarButton icon={<Italic className="h-4 w-4" />} label="Курсив" onClick={actions.formatItalic} />
        <ToolbarButton icon={<Underline className="h-4 w-4" />} label="Подчёркнутый" onClick={actions.formatUnderline} />
        <ToolbarButton icon={<Strikethrough className="h-4 w-4" />} label="Зачёркнутый" onClick={actions.formatStrikethrough} />
        <ToolbarButton icon={<Code className="h-4 w-4" />} label="Код" onClick={actions.formatCode} />
        <ToolbarButton icon={<Subscript className="h-4 w-4" />} label="Подстрочный" onClick={actions.formatSubscript} />
        <ToolbarButton icon={<Superscript className="h-4 w-4" />} label="Надстрочный" onClick={actions.formatSuperscript} />
      </ToolbarGroup>
    );
  }

  if (c.showHeadings) {
    groups.push(
      <ToolbarGroup key="headings" label="Заголовки">
        <ToolbarButton icon={<Heading1 className="h-4 w-4" />} label="H1" onClick={() => actions.formatHeading('h1')} />
        <ToolbarButton icon={<Heading2 className="h-4 w-4" />} label="H2" onClick={() => actions.formatHeading('h2')} />
        <ToolbarButton icon={<Heading3 className="h-4 w-4" />} label="H3" onClick={() => actions.formatHeading('h3')} />
      </ToolbarGroup>
    );
  }

  if (c.showLists) {
    groups.push(
      <ToolbarGroup key="lists" label="Списки">
        <ToolbarButton icon={<List className="h-4 w-4" />} label="Маркированный" onClick={actions.formatBulletList} />
        <ToolbarButton icon={<ListOrdered className="h-4 w-4" />} label="Нумерованный" onClick={actions.formatNumberedList} />
        <ToolbarButton icon={<Quote className="h-4 w-4" />} label="Цитата" onClick={actions.formatQuote} />
      </ToolbarGroup>
    );
  }

  if (c.showAlign) {
    groups.push(
      <ToolbarGroup key="align" label="Выравнивание">
        <ToolbarButton icon={<AlignLeft className="h-4 w-4" />} label="Слева" onClick={() => actions.formatAlign('left')} />
        <ToolbarButton icon={<AlignCenter className="h-4 w-4" />} label="Центр" onClick={() => actions.formatAlign('center')} />
        <ToolbarButton icon={<AlignRight className="h-4 w-4" />} label="Справа" onClick={() => actions.formatAlign('right')} />
        <ToolbarButton icon={<AlignJustify className="h-4 w-4" />} label="По ширине" onClick={() => actions.formatAlign('justify')} />
      </ToolbarGroup>
    );
  }

  if (c.showIndent) {
    groups.push(
      <ToolbarGroup key="indent" label="Отступы">
        <ToolbarButton icon={<IndentDecrease className="h-4 w-4" />} label="Уменьшить" onClick={actions.outdent} />
        <ToolbarButton icon={<IndentIncrease className="h-4 w-4" />} label="Увеличить" onClick={actions.indent} />
      </ToolbarGroup>
    );
  }

  if (c.showFontSize) {
    const handleFontSize = (size: string) => {
      actions.applyFontSize(size);
      onFontSizeChange?.(size);
    };
    const handleLineHeight = (height: string) => {
      actions.applyLineHeight(height);
      onLineHeightChange?.(height);
    };
    groups.push(
      <ToolbarGroup key="font" label="Шрифт">
        <Select onValueChange={handleFontSize} defaultValue="16">
          <SelectTrigger className="h-8 w-[65px] text-xs"><SelectValue placeholder="16" /></SelectTrigger>
          <SelectContent>
            {FONT_SIZES.map((s) => <SelectItem key={s} value={s} className="text-xs">{s}px</SelectItem>)}
          </SelectContent>
        </Select>
        <Select onValueChange={handleLineHeight} defaultValue="1.5">
          <SelectTrigger className="h-8 w-[60px] text-xs"><SelectValue placeholder="1.5" /></SelectTrigger>
          <SelectContent>
            {LINE_HEIGHTS.map((h) => <SelectItem key={h} value={h} className="text-xs">×{h}</SelectItem>)}
          </SelectContent>
        </Select>
      </ToolbarGroup>
    );
  }

  if (c.showInsert) {
    groups.push(
      <ToolbarGroup key="insert" label="Вставка">
        <ToolbarButton icon={<FileCode className="h-4 w-4" />} label="Блок кода" onClick={actions.insertCodeBlock} />
        <ToolbarButton icon={<FileCode2 className="h-4 w-4" />} label="Листинг" onClick={actions.insertSnippet} />
        <ToolbarButton icon={<Image className="h-4 w-4" />} label="Изображение" onClick={actions.insertImage} />
        <ToolbarButton icon={<Minus className="h-4 w-4" />} label="Разделитель" onClick={actions.insertHorizontalRule} />
      </ToolbarGroup>
    );
  }

  // Добавляем сепараторы между группами
  const withSeparators = groups.flatMap((g, i) => 
    i < groups.length - 1 
      ? [g, <Separator key={`sep-${i}`} orientation="vertical" className="h-10 mx-1" />]
      : [g]
  );

  return (
    <div className={cn("flex flex-wrap items-end gap-2 p-2 border-b bg-muted/40", className)}>
      {withSeparators}
      {c.showSave && onSave && (
        <>
          <div className="flex-1" />
          <Button variant="default" size="sm" onClick={onSave} disabled={isSaving} className="gap-1.5 h-8">
            <Save className="h-4 w-4" />
            {isSaving ? 'Сохранение...' : 'Сохранить'}
          </Button>
        </>
      )}
    </div>
  );
}

export default EditorToolbar;
