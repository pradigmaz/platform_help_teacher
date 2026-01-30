import { $createTextNode, $createLineBreakNode } from 'lexical';
import { $createMathNode } from '../../nodes/MathNode';

/**
 * Парсит inline markdown: **bold**, *italic*, LaTeX формулы \(...\) и $...$
 */
export function $parseInlineMarkdown(text: string): import('lexical').LexicalNode[] {
  const nodes: import('lexical').LexicalNode[] = [];
  
  // First pass: find bold/italic patterns that may contain math
  const outerPatterns = [
    { regex: /\*\*\*([^*]+?)\*\*\*/g, type: 'bold-italic', format: 0b11 },
    { regex: /___([^_]+?)___/g, type: 'bold-italic', format: 0b11 },
    { regex: /\*\*([^*]+?)\*\*/g, type: 'bold', format: 0b1 },
    { regex: /__([^_]+?)__/g, type: 'bold', format: 0b1 },
    { regex: /\*([^*\n]+?)\*/g, type: 'italic', format: 0b10 },
    { regex: /(^|[^a-zA-Z0-9])_([^_\s][^_\n]*?[^_\s])_(?![a-zA-Z0-9])/g, type: 'italic', format: 0b10, captureGroup: 2 },
  ];
  
  // Math patterns
  const mathPatterns = [
    { regex: /\\\(([^)]+?)\\\)/g, type: 'math' },
    { regex: /\$(?!\$)([^$\n]+?)\$(?!\$)/g, type: 'math' },
  ];
  
  // Find all outer matches
  const outerMatches: Array<{
    start: number;
    end: number;
    content: string;
    format: number;
  }> = [];
  
  for (const pattern of outerPatterns) {
    let match;
    pattern.regex.lastIndex = 0;
    while ((match = pattern.regex.exec(text)) !== null) {
      const start = match.index;
      const end = pattern.regex.lastIndex;
      const content = match[(pattern as any).captureGroup || 1];
      
      // Adjust start position for patterns with prefix capture groups
      let adjustedStart = start;
      if ((pattern as any).captureGroup === 2) {
        adjustedStart = start + match[1].length;
      }
      
      // Check for overlaps (prefer longer matches)
      const overlaps = outerMatches.some(m => 
        (adjustedStart >= m.start && adjustedStart < m.end) || 
        (end > m.start && end <= m.end) ||
        (adjustedStart <= m.start && end >= m.end)
      );
      
      if (!overlaps) {
        outerMatches.push({
          start: adjustedStart,
          end,
          content,
          format: pattern.format
        });
      }
    }
  }
  
  // Sort by start position
  outerMatches.sort((a, b) => a.start - b.start);
  
  let lastIndex = 0;
  
  for (const outerMatch of outerMatches) {
    // Add text before match
    if (outerMatch.start > lastIndex) {
      const beforeText = text.slice(lastIndex, outerMatch.start);
      const beforeNodes = $parseTextWithMath(beforeText, mathPatterns);
      nodes.push(...beforeNodes);
    }
    
    // Parse content inside bold/italic for math
    const innerNodes = $parseTextWithMath(outerMatch.content, mathPatterns);
    
    // Apply formatting to non-math nodes
    for (const node of innerNodes) {
      if (node.getType() === 'text') {
        (node as any).setFormat(outerMatch.format);
      }
      nodes.push(node);
    }
    
    lastIndex = outerMatch.end;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    const remainingText = text.slice(lastIndex);
    const remainingNodes = $parseTextWithMath(remainingText, mathPatterns);
    nodes.push(...remainingNodes);
  }
  
  // If no outer matches, just parse for math
  if (outerMatches.length === 0) {
    return $parseTextWithMath(text, mathPatterns);
  }
  
  return nodes;
}

/**
 * Helper function to parse text for math formulas only
 */
function $parseTextWithMath(text: string, mathPatterns: Array<{regex: RegExp, type: string}>): import('lexical').LexicalNode[] {
  const nodes: import('lexical').LexicalNode[] = [];
  
  // Find all math matches
  const mathMatches: Array<{
    start: number;
    end: number;
    content: string;
  }> = [];
  
  for (const pattern of mathPatterns) {
    let match;
    pattern.regex.lastIndex = 0;
    while ((match = pattern.regex.exec(text)) !== null) {
      const start = match.index;
      const end = pattern.regex.lastIndex;
      const content = match[1];
      
      // Check for overlaps
      const overlaps = mathMatches.some(m => 
        (start >= m.start && start < m.end) || 
        (end > m.start && end <= m.end) ||
        (start <= m.start && end >= m.end)
      );
      
      if (!overlaps) {
        mathMatches.push({ start, end, content });
      }
    }
  }
  
  // Sort by start position
  mathMatches.sort((a, b) => a.start - b.start);
  
  let lastIndex = 0;
  
  for (const mathMatch of mathMatches) {
    // Add text before match
    if (mathMatch.start > lastIndex) {
      const beforeText = text.slice(lastIndex, mathMatch.start);
      if (beforeText) {
        nodes.push($createTextNode(beforeText));
      }
    }
    
    // Add math node
    nodes.push($createMathNode(mathMatch.content, false));
    lastIndex = mathMatch.end;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    const remainingText = text.slice(lastIndex);
    if (remainingText) {
      nodes.push($createTextNode(remainingText));
    }
  }
  
  // If no math matches, return original text
  if (mathMatches.length === 0 && text) {
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
