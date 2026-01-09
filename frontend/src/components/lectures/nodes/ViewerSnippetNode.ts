import { type LexicalEditor, type EditorConfig, type NodeKey } from 'lexical';
import { createElement, type JSX } from 'react';
import { SnippetNode, type SnippetLanguage, type SerializedSnippetNode } from './SnippetNode';

/**
 * ViewerSnippetNode — версия SnippetNode для read-only просмотра.
 * Рендерит CodeSnippet компонент.
 */
export class ViewerSnippetNode extends SnippetNode {
  static getType(): string {
    return 'snippet';
  }

  static clone(node: ViewerSnippetNode): ViewerSnippetNode {
    return new ViewerSnippetNode(
      node.__code,
      node.__language,
      node.__caption,
      node.__showLineNumbers,
      node.__key
    );
  }

  static importJSON(serializedNode: SerializedSnippetNode): ViewerSnippetNode {
    return new ViewerSnippetNode(
      serializedNode.code,
      serializedNode.language,
      serializedNode.caption,
      serializedNode.showLineNumbers
    );
  }

  constructor(
    code: string = '',
    language: SnippetLanguage = 'javascript',
    caption: string = '',
    showLineNumbers: boolean = true,
    key?: NodeKey
  ) {
    super(code, language, caption, showLineNumbers, key);
  }

  decorate(_editor: LexicalEditor, config: EditorConfig): JSX.Element {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { CodeSnippet } = require('@/components/ui/code-snippet');
    return createElement(CodeSnippet, {
      code: this.__code,
      language: this.__language,
      caption: this.__caption || undefined,
      showLineNumbers: this.__showLineNumbers,
    });
  }
}
