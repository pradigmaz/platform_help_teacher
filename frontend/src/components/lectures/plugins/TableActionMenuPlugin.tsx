'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
} from 'lexical';
import {
  $isTableCellNode,
  $insertTableRow__EXPERIMENTAL,
  $insertTableColumn__EXPERIMENTAL,
  $deleteTableRow__EXPERIMENTAL,
  $deleteTableColumn__EXPERIMENTAL,
} from '@lexical/table';
import { $findMatchingParent } from '@lexical/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Plus, Trash2, ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from 'lucide-react';

export function TableActionMenuPlugin(): React.ReactElement | null {
  const [editor] = useLexicalComposerContext();
  const [menuPosition, setMenuPosition] = useState<{ x: number; y: number } | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const rootElement = editor.getRootElement();
    if (!rootElement) return;

    const handleContextMenu = (e: MouseEvent) => {
      editor.getEditorState().read(() => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) return;
        
        const anchor = selection.anchor.getNode();
        const cellNode = $findMatchingParent(anchor, $isTableCellNode);
        
        if (cellNode) {
          e.preventDefault();
          setMenuPosition({ x: e.clientX, y: e.clientY });
          setIsOpen(true);
        }
      });
    };

    rootElement.addEventListener('contextmenu', handleContextMenu);
    return () => rootElement.removeEventListener('contextmenu', handleContextMenu);
  }, [editor]);

  const insertRowAbove = useCallback(() => {
    editor.update(() => { $insertTableRow__EXPERIMENTAL(false); });
    setIsOpen(false);
  }, [editor]);

  const insertRowBelow = useCallback(() => {
    editor.update(() => { $insertTableRow__EXPERIMENTAL(true); });
    setIsOpen(false);
  }, [editor]);

  const insertColumnLeft = useCallback(() => {
    editor.update(() => { $insertTableColumn__EXPERIMENTAL(false); });
    setIsOpen(false);
  }, [editor]);

  const insertColumnRight = useCallback(() => {
    editor.update(() => { $insertTableColumn__EXPERIMENTAL(true); });
    setIsOpen(false);
  }, [editor]);

  const deleteRow = useCallback(() => {
    editor.update(() => { $deleteTableRow__EXPERIMENTAL(); });
    setIsOpen(false);
  }, [editor]);

  const deleteColumn = useCallback(() => {
    editor.update(() => { $deleteTableColumn__EXPERIMENTAL(); });
    setIsOpen(false);
  }, [editor]);

  if (!menuPosition) return null;

  return createPortal(
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <div
          style={{
            position: 'fixed',
            top: menuPosition.y,
            left: menuPosition.x,
            width: 1,
            height: 1,
          }}
        />
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-52" align="start">
        <DropdownMenuSub>
          <DropdownMenuSubTrigger>
            <Plus className="h-4 w-4 mr-2" />
            Добавить строку
          </DropdownMenuSubTrigger>
          <DropdownMenuSubContent className="w-44">
            <DropdownMenuItem onClick={insertRowAbove}>
              <ArrowUp className="h-4 w-4 mr-2" />
              Выше
            </DropdownMenuItem>
            <DropdownMenuItem onClick={insertRowBelow}>
              <ArrowDown className="h-4 w-4 mr-2" />
              Ниже
            </DropdownMenuItem>
          </DropdownMenuSubContent>
        </DropdownMenuSub>
        
        <DropdownMenuSub>
          <DropdownMenuSubTrigger>
            <Plus className="h-4 w-4 mr-2" />
            Добавить столбец
          </DropdownMenuSubTrigger>
          <DropdownMenuSubContent className="w-44">
            <DropdownMenuItem onClick={insertColumnLeft}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Слева
            </DropdownMenuItem>
            <DropdownMenuItem onClick={insertColumnRight}>
              <ArrowRight className="h-4 w-4 mr-2" />
              Справа
            </DropdownMenuItem>
          </DropdownMenuSubContent>
        </DropdownMenuSub>
        
        <DropdownMenuSeparator />
        
        <DropdownMenuItem onClick={deleteRow} className="text-destructive focus:text-destructive">
          <Trash2 className="h-4 w-4 mr-2" />
          Удалить строку
        </DropdownMenuItem>
        <DropdownMenuItem onClick={deleteColumn} className="text-destructive focus:text-destructive">
          <Trash2 className="h-4 w-4 mr-2" />
          Удалить столбец
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>,
    document.body
  );
}

export default TableActionMenuPlugin;
