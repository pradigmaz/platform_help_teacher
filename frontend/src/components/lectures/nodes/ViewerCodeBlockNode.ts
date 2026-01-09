import { type LexicalEditor, type EditorConfig, type NodeKey } from 'lexical';
import { createElement, type JSX } from 'react';
import { CodeBlockNode, type CodeLanguage, type RenderMode, type SerializedCodeBlockNode } from './CodeBlockNode';

/**
 * ViewerCodeBlockNode — версия CodeBlockNode для read-only просмотра.
 * Рендерит CodeBlockViewerComponent вместо CodeBlockComponent.
 */
export class ViewerCodeBlockNode extends CodeBlockNode {
  static getType(): string {
    return 'code-block'; // Тот же тип, чтобы десериализация работала
  }

  static clone(node: ViewerCodeBlockNode): ViewerCodeBlockNode {
    const cloned = new ViewerCodeBlockNode(
      node.__code,
      node.__language,
      node.__renderMode,
      node.__key
    );
    cloned.__hideCodeForStudents = node.__hideCodeForStudents;
    return cloned;
  }

  static importJSON(serializedNode: SerializedCodeBlockNode): ViewerCodeBlockNode {
    const node = new ViewerCodeBlockNode(
      serializedNode.code,
      serializedNode.language,
      serializedNode.renderMode
    );
    node.__hideCodeForStudents = serializedNode.hideCodeForStudents ?? false;
    return node;
  }

  constructor(
    code: string = '',
    language: CodeLanguage = 'javascript',
    renderMode: RenderMode = 'code',
    key?: NodeKey
  ) {
    super(code, language, renderMode, key);
  }

  decorate(_editor: LexicalEditor, config: EditorConfig): JSX.Element {
    // Динамический импорт Viewer компонента
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { CodeBlockViewerComponent } = require('../CodeBlockViewerComponent');
    return createElement(CodeBlockViewerComponent, {
      code: this.__code,
      language: this.__language,
      renderMode: this.__renderMode,
      hideCodeForStudents: this.__hideCodeForStudents,
    });
  }
}
