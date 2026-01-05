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

export type SnippetLanguage = 
  | 'javascript' 
  | 'typescript' 
  | 'python' 
  | 'html' 
  | 'css' 
  | 'sql'
  | 'json'
  | 'bash'
  | 'plaintext';

export type SerializedSnippetNode = Spread<
  {
    code: string;
    language: SnippetLanguage;
    caption: string;
    showLineNumbers: boolean;
  },
  SerializedLexicalNode
>;

export class SnippetNode extends DecoratorNode<JSX.Element> {
  __code: string;
  __language: SnippetLanguage;
  __caption: string;
  __showLineNumbers: boolean;

  static getType(): string {
    return 'snippet';
  }

  static clone(node: SnippetNode): SnippetNode {
    return new SnippetNode(
      node.__code,
      node.__language,
      node.__caption,
      node.__showLineNumbers,
      node.__key
    );
  }

  static importJSON(serializedNode: SerializedSnippetNode): SnippetNode {
    return $createSnippetNode(
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
    super(key);
    this.__code = code;
    this.__language = language;
    this.__caption = caption;
    this.__showLineNumbers = showLineNumbers;
  }

  exportJSON(): SerializedSnippetNode {
    return {
      ...super.exportJSON(),
      type: 'snippet',
      code: this.__code,
      language: this.__language,
      caption: this.__caption,
      showLineNumbers: this.__showLineNumbers,
      version: 1,
    };
  }

  createDOM(config: EditorConfig): HTMLElement {
    const div = document.createElement('div');
    div.className = 'snippet-wrapper my-4';
    return div;
  }

  updateDOM(): false {
    return false;
  }

  getCode(): string {
    return this.getLatest().__code;
  }

  getLanguage(): SnippetLanguage {
    return this.getLatest().__language;
  }

  getCaption(): string {
    return this.getLatest().__caption;
  }

  getShowLineNumbers(): boolean {
    return this.getLatest().__showLineNumbers;
  }

  setCode(code: string): this {
    const writable = this.getWritable();
    writable.__code = code;
    return writable;
  }

  setLanguage(language: SnippetLanguage): this {
    const writable = this.getWritable();
    writable.__language = language;
    return writable;
  }

  setCaption(caption: string): this {
    const writable = this.getWritable();
    writable.__caption = caption;
    return writable;
  }

  setShowLineNumbers(show: boolean): this {
    const writable = this.getWritable();
    writable.__showLineNumbers = show;
    return writable;
  }

  decorate(_editor: LexicalEditor, config: EditorConfig): JSX.Element {
    const { SnippetComponent } = require('../SnippetComponent');
    return createElement(SnippetComponent, {
      nodeKey: this.__key,
      code: this.__code,
      language: this.__language,
      caption: this.__caption,
      showLineNumbers: this.__showLineNumbers,
    });
  }
}

export function $createSnippetNode(
  code: string = '',
  language: SnippetLanguage = 'javascript',
  caption: string = '',
  showLineNumbers: boolean = true
): SnippetNode {
  return $applyNodeReplacement(new SnippetNode(code, language, caption, showLineNumbers));
}

export function $isSnippetNode(
  node: LexicalNode | null | undefined
): node is SnippetNode {
  return node instanceof SnippetNode;
}
