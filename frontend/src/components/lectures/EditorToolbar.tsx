'use client';

import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { Button } from '@/components/ui/button';
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
import {
  ToolbarButton,
  ToolbarGroup,
  useToolbarActions,
  FONT_SIZES,
  LINE_HEIGHTS,
} from './toolbar';

interface EditorToolbarProps {
  onSave?: () => void;
  isSaving?: boolean;
  className?: string;
}

export function EditorToolbar({ onSave, isSaving, className }: EditorToolbarProps) {
  const [editor] = useLexicalComposerContext();
  const actions = useToolbarActions(editor);

  return (
    <div className={cn(
      "flex flex-wrap items-end gap-3 p-3 border-b bg-muted/40",
      className
    )}>
      {/* История */}
      <ToolbarGroup label="История">
        <ToolbarButton icon={<Undo className="h-4 w-4" />} label="Отменить (Ctrl+Z)" onClick={actions.undo} />
        <ToolbarButton icon={<Redo className="h-4 w-4" />} label="Повторить (Ctrl+Y)" onClick={actions.redo} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Форматирование текста */}
      <ToolbarGroup label="Текст">
        <ToolbarButton icon={<Bold className="h-4 w-4" />} label="Жирный (Ctrl+B)" onClick={actions.formatBold} />
        <ToolbarButton icon={<Italic className="h-4 w-4" />} label="Курсив (Ctrl+I)" onClick={actions.formatItalic} />
        <ToolbarButton icon={<Underline className="h-4 w-4" />} label="Подчёркнутый (Ctrl+U)" onClick={actions.formatUnderline} />
        <ToolbarButton icon={<Strikethrough className="h-4 w-4" />} label="Зачёркнутый" onClick={actions.formatStrikethrough} />
        <ToolbarButton icon={<Code className="h-4 w-4" />} label="Код" onClick={actions.formatCode} />
        <ToolbarButton icon={<Subscript className="h-4 w-4" />} label="Подстрочный" onClick={actions.formatSubscript} />
        <ToolbarButton icon={<Superscript className="h-4 w-4" />} label="Надстрочный" onClick={actions.formatSuperscript} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Заголовки */}
      <ToolbarGroup label="Заголовки">
        <ToolbarButton icon={<Heading1 className="h-4 w-4" />} label="Заголовок 1" onClick={() => actions.formatHeading('h1')} />
        <ToolbarButton icon={<Heading2 className="h-4 w-4" />} label="Заголовок 2" onClick={() => actions.formatHeading('h2')} />
        <ToolbarButton icon={<Heading3 className="h-4 w-4" />} label="Заголовок 3" onClick={() => actions.formatHeading('h3')} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Списки */}
      <ToolbarGroup label="Списки">
        <ToolbarButton icon={<List className="h-4 w-4" />} label="Маркированный" onClick={actions.formatBulletList} />
        <ToolbarButton icon={<ListOrdered className="h-4 w-4" />} label="Нумерованный" onClick={actions.formatNumberedList} />
        <ToolbarButton icon={<Quote className="h-4 w-4" />} label="Цитата" onClick={actions.formatQuote} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Выравнивание */}
      <ToolbarGroup label="Выравнивание">
        <ToolbarButton icon={<AlignLeft className="h-4 w-4" />} label="По левому краю" onClick={() => actions.formatAlign('left')} />
        <ToolbarButton icon={<AlignCenter className="h-4 w-4" />} label="По центру" onClick={() => actions.formatAlign('center')} />
        <ToolbarButton icon={<AlignRight className="h-4 w-4" />} label="По правому краю" onClick={() => actions.formatAlign('right')} />
        <ToolbarButton icon={<AlignJustify className="h-4 w-4" />} label="По ширине" onClick={() => actions.formatAlign('justify')} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Отступы */}
      <ToolbarGroup label="Отступы">
        <ToolbarButton icon={<IndentDecrease className="h-4 w-4" />} label="Уменьшить" onClick={actions.outdent} />
        <ToolbarButton icon={<IndentIncrease className="h-4 w-4" />} label="Увеличить" onClick={actions.indent} />
      </ToolbarGroup>
      
      <Separator orientation="vertical" className="h-12 mx-1" />
      
      {/* Размер и интервал */}
      <ToolbarGroup label="Шрифт">
        <Select onValueChange={actions.applyFontSize} defaultValue="16">
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
        <Select onValueChange={actions.applyLineHeight} defaultValue="1.5">
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
        <ToolbarButton icon={<FileCode className="h-4 w-4" />} label="Блок кода (визуализация)" onClick={actions.insertCodeBlock} />
        <ToolbarButton icon={<FileCode2 className="h-4 w-4" />} label="Листинг (пример кода)" onClick={actions.insertSnippet} />
        <ToolbarButton icon={<Image className="h-4 w-4" />} label="Изображение" onClick={actions.insertImage} />
        <ToolbarButton icon={<Minus className="h-4 w-4" />} label="Разделитель (---)" onClick={actions.insertHorizontalRule} />
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
