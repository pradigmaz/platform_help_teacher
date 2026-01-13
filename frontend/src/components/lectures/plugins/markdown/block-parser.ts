import { $createParagraphNode } from 'lexical';
import { $createHeadingNode, $createQuoteNode } from '@lexical/rich-text';
import { $createListNode, $createListItemNode } from '@lexical/list';
import { $parseInlineMarkdown } from './inline-parser';

/**
 * Парсит строку markdown в Lexical node (заголовок, список, цитата, параграф)
 */
export function $parseMarkdownLine(line: string): import('lexical').LexicalNode | null {
  if (!line.trim()) return null;
  
  // Заголовки
  const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
  if (headingMatch) {
    const level = headingMatch[1].length as 1 | 2 | 3 | 4 | 5 | 6;
    const heading = $createHeadingNode(`h${level}`);
    const formattedNodes = $parseInlineMarkdown(headingMatch[2]);
    for (const node of formattedNodes) {
      heading.append(node);
    }
    return heading;
  }
  
  // Цитаты
  const quoteMatch = line.match(/^>\s*(.*)$/);
  if (quoteMatch) {
    const quote = $createQuoteNode();
    const formattedNodes = $parseInlineMarkdown(quoteMatch[1]);
    for (const node of formattedNodes) {
      quote.append(node);
    }
    return quote;
  }
  
  // Маркированный список
  const ulMatch = line.match(/^[-*]\s+(.+)$/);
  if (ulMatch) {
    const list = $createListNode('bullet');
    const item = $createListItemNode();
    const formattedNodes = $parseInlineMarkdown(ulMatch[1]);
    for (const node of formattedNodes) {
      item.append(node);
    }
    list.append(item);
    return list;
  }
  
  // Нумерованный список
  const olMatch = line.match(/^\d+\.\s+(.+)$/);
  if (olMatch) {
    const list = $createListNode('number');
    const item = $createListItemNode();
    const formattedNodes = $parseInlineMarkdown(olMatch[1]);
    for (const node of formattedNodes) {
      item.append(node);
    }
    list.append(item);
    return list;
  }
  
  // Обычный параграф
  const paragraph = $createParagraphNode();
  const formattedNodes = $parseInlineMarkdown(line);
  for (const node of formattedNodes) {
    paragraph.append(node);
  }
  return paragraph;
}
