import { $createTextNode, $createLineBreakNode } from 'lexical';

/**
 * Парсит inline markdown: **bold**, __bold__, *italic*, _italic_, ***bold italic***
 */
export function $parseInlineMarkdown(text: string): import('lexical').LexicalNode[] {
  const nodes: import('lexical').LexicalNode[] = [];
  
  // Regex for:
  // - bold+italic: ***text*** or ___text___
  // - bold: **text** or __text__
  // - italic: *text* or _text_ (but not inside words for underscore)
  const regex = /(\*\*\*(.+?)\*\*\*|___(.+?)___|__(.+?)__|_([^_\s][^_]*[^_\s])_|\*\*(.+?)\*\*|\*([^*\s][^*]*[^*\s]|\S)\*)/g;
  
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
    
    // Determine which group matched and create formatted text node
    let content: string;
    let format: number;
    
    if (match[2]) {
      // ***bold italic*** with asterisks
      content = match[2];
      format = 0b11; // bold + italic
    } else if (match[3]) {
      // ___bold italic___ with underscores
      content = match[3];
      format = 0b11; // bold + italic
    } else if (match[4]) {
      // __bold__ with underscores
      content = match[4];
      format = 0b1; // bold
    } else if (match[5]) {
      // _italic_ with underscores
      content = match[5];
      format = 0b10; // italic
    } else if (match[6]) {
      // **bold** with asterisks
      content = match[6];
      format = 0b1; // bold
    } else if (match[7]) {
      // *italic* with asterisks
      content = match[7];
      format = 0b10; // italic
    } else {
      continue;
    }
    
    const textNode = $createTextNode(content);
    textNode.setFormat(format);
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
