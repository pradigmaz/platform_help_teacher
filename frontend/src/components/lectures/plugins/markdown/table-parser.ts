import { $createParagraphNode } from 'lexical';
import { $createTableNode, $createTableRowNode, $createTableCellNode, TableCellHeaderStates } from '@lexical/table';
import { $createFormattedCellContent } from './inline-parser';

export interface MarkdownTableData {
  headers: string[];
  rows: string[][];
}

/**
 * Парсит markdown таблицу в структурированные данные
 */
export function parseMarkdownTable(tableText: string): MarkdownTableData | null {
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

/**
 * Создаёт Lexical TableNode из распарсенных данных
 */
export function $createTableFromMarkdown(data: MarkdownTableData) {
  const tableNode = $createTableNode();
  
  // Header row
  const headerRow = $createTableRowNode();
  for (const header of data.headers) {
    const cell = $createTableCellNode(TableCellHeaderStates.ROW);
    const paragraph = $createParagraphNode();
    const contentNodes = $createFormattedCellContent(header);
    for (const node of contentNodes) {
      paragraph.append(node);
    }
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
      const contentNodes = $createFormattedCellContent(cellText);
      for (const node of contentNodes) {
        paragraph.append(node);
      }
      cell.append(paragraph);
      tableRow.append(cell);
    }
    tableNode.append(tableRow);
  }
  
  return tableNode;
}
