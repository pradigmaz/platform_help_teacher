'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  COMMAND_PRIORITY_LOW,
  SELECTION_CHANGE_COMMAND,
} from 'lexical';
import {
  $isTableCellNode,
  $isTableRowNode,
  $getTableNodeFromLexicalNodeOrThrow,
  $getTableRowIndexFromTableCellNode,
  $getTableColumnIndexFromTableCellNode,
  $insertTableRow__EXPERIMENTAL,
  $insertTableColumn__EXPERIMENTAL,
  $deleteTableRow__EXPERIMENTAL,
  $deleteTableColumn__EXPERIMENTAL,
  TableCellNode,
} from '@lexical/table';
import { $findMatchingParent } from '@lexical/utils';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Plus, Trash2, MoreHorizontal, ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from 'lucide-react';

export function TableActionMenuPlugin(): React.ReactElement | null {
  const [editor] = useLexicalComposerContext();
  const [tableCellNode, setTableCellNode] = useState<TableCellNode | null>(null);
  const [menuPosition, setMenuPosition] = useState<{ top: number; left: number } | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const updateMenu = useCallback(() => {
    editor.getEditorState().read(() => {
      const selection = $getSelection();
      if (!$isRangeSelection(selection)) {
        setTableCellNode(null);
        setMenuPosition(null);
        return;
      }

      const anchor = selection.anchor.getNode();
      const cellNode = $findMatchingParent(anchor, $isTableCellNode) as TableCellNode | null;
      
      if (!cellNode) {
        setTableCellNode(null);
        setMenuPosition(null);
        return;
      }

      setTableCellNode(cellNode);
      
      // Get DOM element position
      const cellElement = editor.getElementByKey(cellNode.getKey());
      if (cellElement) {
        const rect = cellElement.getBoundingClientRect();
        setMenuPosition({
          top: rect.top - 40,
          left: rect.right - 30,
        });
      }
    });
  }, [editor]);

  useEffect(() => {
    return editor.registerCommand(
      SELECTION_CHANGE_COMMAND,
      () => {
        updateMenu();
        return false;
      },
      COMMAND_PRIORITY_LOW
    );
  }, [editor, updateMenu]);

  const insertRowAbove = useCallback(() => {
    editor.update(() => {
      if (tableCellNode) {
        $insertTableRow__EXPERIMENTAL(false);
      }
    });
  }, [editor, tableCellNode]);

  const insertRowBelow = useCallback(() => {
    editor.update(() => {
      if (tableCellNode) {
        $insertTableRow__EXPERIMENTAL(true);
      }
    });
  }, [editor, tableCellNode]);

  const insertColumnLeft = useCallback(() => {
    editor.update(() => {
      if (tableCellNode) {
        $insertTableColumn__EXPERIMENTAL(false);
      }
    });
  }, [editor, tableCellNode]);

  const insertColumnRight = useCallback(() => {
    editor.update(() => {
      if (tableCellNode) {
        $insertTableColumn__EXPERIMENTAL(true);
      }
    });
  }, [editor, tableCellNode]);

  const deleteRow = useCallback(() => {
    editor.update(() => {
      if (tableCellNode) {
        $deleteTableRow__EXPERIMENTAL();
      }
    });
  }, [editor, tableCellNode]);

  const deleteColumn = useCallback(() => {
    editor.update(() => {
      if (tableCellNode) {
        $deleteTableColumn__EXPERIMENTAL();
      }
    });
  }, [editor, tableCellNode]);

  if (!tableCellNode || !menuPosition) {
    return null;
  }

  return (
    <div
      ref={menuRef}
      className="fixed z-50"
      style={{ top: menuPosition.top, left: menuPosition.left }}
    >
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="icon" className="h-7 w-7 bg-background shadow-md">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuItem onClick={insertRowAbove}>
            <ArrowUp className="h-4 w-4 mr-2" />
            Строка выше
          </DropdownMenuItem>
          <DropdownMenuItem onClick={insertRowBelow}>
            <ArrowDown className="h-4 w-4 mr-2" />
            Строка ниже
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={insertColumnLeft}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Столбец слева
          </DropdownMenuItem>
          <DropdownMenuItem onClick={insertColumnRight}>
            <ArrowRight className="h-4 w-4 mr-2" />
            Столбец справа
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={deleteRow} className="text-destructive">
            <Trash2 className="h-4 w-4 mr-2" />
            Удалить строку
          </DropdownMenuItem>
          <DropdownMenuItem onClick={deleteColumn} className="text-destructive">
            <Trash2 className="h-4 w-4 mr-2" />
            Удалить столбец
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

export default TableActionMenuPlugin;
