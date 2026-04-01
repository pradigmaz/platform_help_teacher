import {
  DecoratorNode,
  type LexicalNode,
  type NodeKey,
  type SerializedLexicalNode,
  type Spread,
  $applyNodeReplacement,
} from 'lexical';
import { createElement, type JSX } from 'react';

export type SerializedMathNode = Spread<
  {
    latex: string;
    displayMode: boolean;
  },
  SerializedLexicalNode
>;

export class MathNode extends DecoratorNode<JSX.Element> {
  __latex: string;
  __displayMode: boolean;

  static getType(): string {
    return 'math';
  }

  static clone(node: MathNode): MathNode {
    return new MathNode(node.__latex, node.__displayMode, node.__key);
  }

  static importJSON(serializedNode: SerializedMathNode): MathNode {
    return $createMathNode(serializedNode.latex, serializedNode.displayMode);
  }

  constructor(latex: string = '', displayMode: boolean = false, key?: NodeKey) {
    super(key);
    this.__latex = latex;
    this.__displayMode = displayMode;
  }

  exportJSON(): SerializedMathNode {
    return {
      ...super.exportJSON(),
      type: 'math',
      latex: this.__latex,
      displayMode: this.__displayMode,
      version: 1,
    };
  }

  createDOM(): HTMLElement {
    const tag = this.__displayMode ? 'div' : 'span';
    const element = document.createElement(tag);
    element.className = this.__displayMode ? 'math-block my-4' : 'math-inline';
    return element;
  }

  updateDOM(): false {
    return false;
  }

  getLatex(): string {
    return this.getLatest().__latex;
  }

  getDisplayMode(): boolean {
    return this.getLatest().__displayMode;
  }

  setLatex(latex: string): this {
    const writable = this.getWritable();
    writable.__latex = latex;
    return writable;
  }

  setDisplayMode(displayMode: boolean): this {
    const writable = this.getWritable();
    writable.__displayMode = displayMode;
    return writable;
  }

  isInline(): boolean {
    return !this.__displayMode;
  }

  getTextContent(): string {
    return this.__displayMode ? `$$${this.__latex}$$` : `$${this.__latex}$`;
  }

  decorate(): JSX.Element {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { MathComponent } = require('../MathComponent');
    return createElement(MathComponent, {
      nodeKey: this.__key,
      latex: this.__latex,
      displayMode: this.__displayMode,
    });
  }
}

export function $createMathNode(latex: string = '', displayMode: boolean = false): MathNode {
  return $applyNodeReplacement(new MathNode(latex, displayMode));
}

export function $isMathNode(node: LexicalNode | null | undefined): node is MathNode {
  return node instanceof MathNode;
}
