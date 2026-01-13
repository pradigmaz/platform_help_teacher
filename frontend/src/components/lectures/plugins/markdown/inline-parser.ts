import { $createTextNode, $createLineBreakNode } from 'lexical';

/**
 * Парсит inline markdown: **bold**, *italic*, ***bold italic***
 */
export function $parseInlineMarkdown(text: string): import('lexical').LexicalNode[] {
  const nodes: import('lexical').LexicalNode[] = [];
  
  // Regex for bold+italic (***text***), bold (**text**), italic (*text*)
  const regex = /(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*)/g;
  
  let lastIndex = 0;
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      const beforeText = text.slice(lastIndex, match.index);
      if (beforeText) {
        nodes.push($createTextNode(beforeText));
      }
    }
    
    // Create formatted text node
    const textNode = $createTextNode(match[2] || match[3] || match[4]);
    
    if (match[2]) {
      // ***bold italic***
      textNode.setFormat(0b11); // bold + italic
    } else if (match[3]) {
      // **bold**
      textNode.setFormat(0b1); // bold
    } else if (match[4]) {
      // *italic*
      textNode.setFormat(0b10); // italic
    }
    
    nodes.push(textNode);
    lastIndex = regex.lastIndex;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    const remainingText = text.slice(lastIndex);
    if (remainingText) {
      nodes.push($createTextNode(remainingText));
    }
  }
  
  // If no matches, return original text
  if (nodes.length === 0 && text) {
    nodes.push($createTextNode(text));
  }
  
  return nodes;
}

/**
 * Парсит текст ячейки с поддержкой <br>, **bold**, *italic*
 */
export function $createFormattedCellContent(cellText: string): import('lexical').LexicalNode[] {
  const nodes: import('lexical').LexicalNode[] = [];
  
  // Split by <br> or <br/> tags
  const parts = cellText.split(/<br\s*\/?>/gi);
  
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    
    // Parse inline markdown in each part
    const textNodes = $parseInlineMarkdown(part);
    nodes.push(...textNodes);
    
    // Add line break between parts (not after last)
    if (i < parts.length - 1) {
      nodes.push($createLineBreakNode());
    }
  }
  
  return nodes;
}
