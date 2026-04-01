import { type NodeKey } from 'lexical';
import { createElement, type JSX } from 'react';
import { MathNode, type SerializedMathNode } from './MathNode';

/**
 * ViewerMathNode — версия MathNode для read-only просмотра.
 */
export class ViewerMathNode extends MathNode {
  static getType(): string {
    return 'math'; // Тот же тип для десериализации
  }

  static clone(node: ViewerMathNode): ViewerMathNode {
    return new ViewerMathNode(node.__latex, node.__displayMode, node.__key);
  }

  static importJSON(serializedNode: SerializedMathNode): ViewerMathNode {
    return new ViewerMathNode(serializedNode.latex, serializedNode.displayMode);
  }

  constructor(latex: string = '', displayMode: boolean = false, key?: NodeKey) {
    super(latex, displayMode, key);
  }

  decorate(): JSX.Element {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { MathViewerComponent } = require('../MathViewerComponent');
    return createElement(MathViewerComponent, {
      latex: this.__latex,
      displayMode: this.__displayMode,
    });
  }
}
