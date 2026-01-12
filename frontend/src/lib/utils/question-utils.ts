import { SerializedEditorState } from 'lexical';

export interface QuestionData {
  text?: string;
  content?: SerializedEditorState | Record<string, unknown>;
}

/**
 * Извлекает текст из вопроса (поддерживает legacy string и новый формат с Lexical)
 */
export function getQuestionText(question: string | QuestionData): string {
  if (typeof question === 'string') {
    return question;
  }
  
  // Новый формат — сначала пробуем text, потом извлекаем из content
  if (question.text) {
    return question.text;
  }
  
  if (question.content) {
    return extractTextFromLexical(question.content as SerializedEditorState);
  }
  
  return '';
}

/**
 * Извлекает plain text из Lexical state
 */
function extractTextFromLexical(state: SerializedEditorState): string {
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
