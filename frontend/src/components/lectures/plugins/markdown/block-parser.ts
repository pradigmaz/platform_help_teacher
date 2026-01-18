import { $createParagraphNode, type LexicalNode } from 'lexical';
import { $createHeadingNode, $createQuoteNode } from '@lexical/rich-text';
import { $createListNode, $createListItemNode, ListNode } from '@lexical/list';
import { $parseInlineMarkdown } from './inline-parser';

type LineType = 'heading' | 'quote' | 'bullet' | 'number' | 'paragraph' | 'empty';

interface ParsedLine {
  type: LineType;
  content: string;
  level?: number; // для заголовков
}

/**
 * Определяет тип строки markdown
 */
function getLineType(line: string): ParsedLine {
  const trimmed = line.trim();
  if (!trimmed) return { type: 'empty', content: '' };
  
  // Заголовки
  const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
  if (headingMatch) {
    return { type: 'heading', content: headingMatch[2], level: headingMatch[1].length };
  }
  
  // Цитаты
  const quoteMatch = trimmed.match(/^>\s*(.*)$/);
  if (quoteMatch) {
    return { type: 'quote', content: quoteMatch[1] };
  }
  
  // Маркированный список
  const ulMatch = trimmed.match(/^[-*]\s+(.+)$/);
  if (ulMatch) {
    return { type: 'bullet', content: ulMatch[1] };
  }
  
  // Нумерованный список
  const olMatch = trimmed.match(/^\d+\.\s+(.+)$/);
  if (olMatch) {
    return { type: 'number', content: olMatch[1] };
  }
  
  return { type: 'paragraph', content: trimmed };
}

/**
 * Парсит строку markdown в Lexical node (заголовок, список, цитата, параграф)
 * @deprecated Используй $parseMarkdownLines для корректной группировки списков
 */
export function $parseMarkdownLine(line: string): LexicalNode | null {
  const parsed = getLineType(line);
  if (parsed.type === 'empty') return null;
  
  switch (parsed.type) {
    case 'heading': {
      const heading = $createHeadingNode(`h${parsed.level}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6');
      const formattedNodes = $parseInlineMarkdown(parsed.content);
      for (const node of formattedNodes) heading.append(node);
      return heading;
    }
    case 'quote': {
      const quote = $createQuoteNode();
      const formattedNodes = $parseInlineMarkdown(parsed.content);
      for (const node of formattedNodes) quote.append(node);
      return quote;
    }
    case 'bullet':
    case 'number': {
      const list = $createListNode(parsed.type === 'bullet' ? 'bullet' : 'number');
      const item = $createListItemNode();
      const formattedNodes = $parseInlineMarkdown(parsed.content);
      for (const node of formattedNodes) item.append(node);
      list.append(item);
      return list;
    }
    default: {
      const paragraph = $createParagraphNode();
      const formattedNodes = $parseInlineMarkdown(parsed.content);
      for (const node of formattedNodes) paragraph.append(node);
      return paragraph;
    }
  }
}

/**
 * Парсит массив строк markdown с группировкой последовательных элементов списка
 */
export function $parseMarkdownLines(lines: string[]): LexicalNode[] {
  const nodes: LexicalNode[] = [];
  let currentList: ListNode | null = null;
  let currentListType: 'bullet' | 'number' | null = null;
  
  for (const line of lines) {
    const parsed = getLineType(line);
    
    // Пустая строка — сбрасываем текущий список
    if (parsed.type === 'empty') {
      currentList = null;
      currentListType = null;
      continue;
    }
    
    // Элемент списка
    if (parsed.type === 'bullet' || parsed.type === 'number') {
      const listType = parsed.type === 'bullet' ? 'bullet' : 'number';
      
      // Если тип списка изменился или списка нет — создаём новый
      if (!currentList || currentListType !== listType) {
        currentList = $createListNode(listType);
        currentListType = listType;
        nodes.push(currentList);
      }
      
      // Добавляем элемент в текущий список
      const item = $createListItemNode();
      const formattedNodes = $parseInlineMarkdown(parsed.content);
      for (const node of formattedNodes) item.append(node);
      currentList.append(item);
      continue;
    }
    
    // Любой другой тип — сбрасываем список
    currentList = null;
    currentListType = null;
    
    switch (parsed.type) {
      case 'heading': {
        const heading = $createHeadingNode(`h${parsed.level}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6');
        const formattedNodes = $parseInlineMarkdown(parsed.content);
        for (const node of formattedNodes) heading.append(node);
        nodes.push(heading);
        break;
      }
      case 'quote': {
        const quote = $createQuoteNode();
        const formattedNodes = $parseInlineMarkdown(parsed.content);
        for (const node of formattedNodes) quote.append(node);
        nodes.push(quote);
        break;
      }
      default: {
        const paragraph = $createParagraphNode();
        const formattedNodes = $parseInlineMarkdown(parsed.content);
        for (const node of formattedNodes) paragraph.append(node);
        nodes.push(paragraph);
      }
    }
  }
  
  return nodes;
}
