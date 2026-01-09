import {
  DecoratorNode,
  type EditorConfig,
  type LexicalEditor,
  type LexicalNode,
  type NodeKey,
  type SerializedLexicalNode,
  type Spread,
  $applyNodeReplacement,
} from 'lexical';
import { createElement, type JSX } from 'react';

export type CodeLanguage = 'javascript' | 'python' | 'typescript' | 'html' | 'css' | 'sql';
export type RenderMode = 'code' | 'render';

export type SerializedCodeBlockNode = Spread<
  {
    code: string;
    language: CodeLanguage;
    renderMode: RenderMode;
    hideCodeForStudents: boolean;
    collapsed: boolean;
    caption: string;
  },
  SerializedLexicalNode
>;

// Lazy import для избежания циклических зависимостей
let CodeBlockComponentModule: typeof import('../CodeBlockComponent') | null = null;

async function getCodeBlockComponent() {
  if (!CodeBlockComponentModule) {
    CodeBlockComponentModule = await import('../CodeBlockComponent');
  }
  return CodeBlockComponentModule.CodeBlockComponent;
}

export class CodeBlockNode extends DecoratorNode<JSX.Element> {
  __code: string;
  __language: CodeLanguage;
  __renderMode: RenderMode;
  __hideCodeForStudents: boolean = false;
  __collapsed: boolean = false;
  __caption: string = '';

  static getType(): string {
    return 'code-block';
  }

  static clone(node: CodeBlockNode): CodeBlockNode {
    const cloned = new CodeBlockNode(
      node.__code,
      node.__language,
      node.__renderMode,
      node.__key
    );
    cloned.__hideCodeForStudents = node.__hideCodeForStudents;
    cloned.__collapsed = node.__collapsed;
    cloned.__caption = node.__caption;
    return cloned;
  }

  static importJSON(serializedNode: SerializedCodeBlockNode): CodeBlockNode {
    const node = $createCodeBlockNode(
      serializedNode.code,
      serializedNode.language,
      serializedNode.renderMode
    );
    node.__hideCodeForStudents = serializedNode.hideCodeForStudents ?? false;
    node.__collapsed = serializedNode.collapsed ?? false;
    node.__caption = serializedNode.caption ?? '';
    return node;
  }

  constructor(
    code: string = '',
    language: CodeLanguage = 'javascript',
    renderMode: RenderMode = 'code',
    key?: NodeKey
  ) {
    super(key);
    this.__code = code;
    this.__language = language;
    this.__renderMode = renderMode;
  }

  exportJSON(): SerializedCodeBlockNode {
    return {
      ...super.exportJSON(),
      type: 'code-block',
      code: this.__code,
      language: this.__language,
      renderMode: this.__renderMode,
      hideCodeForStudents: this.__hideCodeForStudents,
      collapsed: this.__collapsed,
      caption: this.__caption,
      version: 1,
    };
  }

  createDOM(config: EditorConfig): HTMLElement {
    const div = document.createElement('div');
    div.className = 'code-block-wrapper my-4';
    div.setAttribute('data-lexical-key', this.__key);
    return div;
  }

  updateDOM(): false {
    return false;
  }

  // Getters
  getCode(): string {
    return this.getLatest().__code;
  }

  getLanguage(): CodeLanguage {
    return this.getLatest().__language;
  }

  getRenderMode(): RenderMode {
    return this.getLatest().__renderMode;
  }

  getHideCodeForStudents(): boolean {
    return this.getLatest().__hideCodeForStudents;
  }

  getCollapsed(): boolean {
    return this.getLatest().__collapsed;
  }

  getCaption(): string {
    return this.getLatest().__caption;
  }

  // Setters (return writable node for chaining)
  setCode(code: string): this {
    const writable = this.getWritable();
    writable.__code = code;
    return writable;
  }

  setLanguage(language: CodeLanguage): this {
    const writable = this.getWritable();
    writable.__language = language;
    return writable;
  }

  setRenderMode(mode: RenderMode): this {
    const writable = this.getWritable();
    writable.__renderMode = mode;
    return writable;
  }

  setHideCodeForStudents(hide: boolean): this {
    const writable = this.getWritable();
    writable.__hideCodeForStudents = hide;
    return writable;
  }

  setCollapsed(collapsed: boolean): this {
    const writable = this.getWritable();
    writable.__collapsed = collapsed;
    return writable;
  }

  toggleCollapsed(): this {
    const writable = this.getWritable();
    writable.__collapsed = !writable.__collapsed;
    return writable;
  }

  setCaption(caption: string): this {
    const writable = this.getWritable();
    writable.__caption = caption;
    return writable;
  }

  toggleRenderMode(): this {
    const writable = this.getWritable();
    writable.__renderMode = writable.__renderMode === 'code' ? 'render' : 'code';
    return writable;
  }

  // Check if code is JavaScript (can be rendered as visualization)
  isRenderable(): boolean {
    return this.__language === 'javascript' || this.__language === 'typescript';
  }

  decorate(_editor: LexicalEditor, config: EditorConfig): JSX.Element {
    // Динамический импорт компонента
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { CodeBlockComponent } = require('../CodeBlockComponent');
    return createElement(CodeBlockComponent, {
      nodeKey: this.__key,
      code: this.__code,
      language: this.__language,
      renderMode: this.__renderMode,
      hideCodeForStudents: this.__hideCodeForStudents,
      collapsed: this.__collapsed,
      caption: this.__caption,
    });
  }
}

export function $createCodeBlockNode(
  code: string = '',
  language: CodeLanguage = 'javascript',
  renderMode: RenderMode = 'code'
): CodeBlockNode {
  return $applyNodeReplacement(new CodeBlockNode(code, language, renderMode));
}

export function $isCodeBlockNode(
  node: LexicalNode | null | undefined
): node is CodeBlockNode {
  return node instanceof CodeBlockNode;
}
