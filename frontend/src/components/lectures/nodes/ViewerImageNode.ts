import { type LexicalEditor, type EditorConfig, type NodeKey } from 'lexical';
import { createElement, type JSX } from 'react';
import { ImageNode, type ImageDimension, type SerializedImageNode } from './ImageNode';

/**
 * ViewerImageNode — версия ImageNode для read-only просмотра.
 * Рендерит ImageViewerComponent вместо ImageComponent.
 */
export class ViewerImageNode extends ImageNode {
  static getType(): string {
    return 'lecture-image'; // Тот же тип, чтобы десериализация работала
  }

  static clone(node: ViewerImageNode): ViewerImageNode {
    return new ViewerImageNode(
      node.__src,
      node.__altText,
      node.__caption,
      node.__width,
      node.__height,
      node.__key
    );
  }

  static importJSON(serializedNode: SerializedImageNode): ViewerImageNode {
    return new ViewerImageNode(
      serializedNode.src,
      serializedNode.altText,
      serializedNode.caption,
      serializedNode.width,
      serializedNode.height
    );
  }

  constructor(
    src: string,
    altText: string = '',
    caption: string = '',
    width: ImageDimension = 'auto',
    height: ImageDimension = 'auto',
    key?: NodeKey
  ) {
    super(src, altText, caption, width, height, key);
  }

  decorate(_editor: LexicalEditor, config: EditorConfig): JSX.Element {
    // Динамический импорт Viewer компонента
    const { ImageViewerComponent } = require('../ImageViewerComponent');
    return createElement(ImageViewerComponent, {
      src: this.__src,
      altText: this.__altText,
      caption: this.__caption,
      width: this.__width,
      height: this.__height,
    });
  }
}
