import type { SerializedEditorState } from 'lexical';

/**
 * Извлекает текст из Lexical SerializedEditorState
 * Используется для превью контента и поиска
 */
export function extractTextFromLexical(state?: SerializedEditorState): string {
  try {
    const root = state?.root;
    if (!root?.children) return '';
    
    let text = '';
    const extractFromNode = (node: Record<string, unknown>) => {
      if (node.text && typeof node.text === 'string') {
        text += node.text;
      }
      if (node.children && Array.isArray(node.children)) {
        node.children.forEach(extractFromNode);
      }
    };
    
    root.children.forEach(extractFromNode);
    return text.trim();
  } catch {
    return '';
  }
}

/**
 * Проверяет, содержит ли Lexical state какой-либо контент
 */
export function hasLexicalContent(state?: SerializedEditorState): boolean {
  return extractTextFromLexical(state).length > 0;
}

/**
 * Обрезает текст до указанной длины с многоточием
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}
