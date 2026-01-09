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

export type ImageDimension = number | 'auto';

export type SerializedImageNode = Spread<
  {
    src: string;
    altText: string;
    caption: string;
    width: ImageDimension;
    height: ImageDimension;
  },
  SerializedLexicalNode
>;

export class ImageNode extends DecoratorNode<JSX.Element> {
  __src: string;
  __altText: string;
  __caption: string;
  __width: ImageDimension;
  __height: ImageDimension;

  static getType(): string {
    return 'lecture-image';
  }

  static clone(node: ImageNode): ImageNode {
    return new ImageNode(
      node.__src,
      node.__altText,
      node.__caption,
      node.__width,
      node.__height,
      node.__key
    );
  }

  static importJSON(serializedNode: SerializedImageNode): ImageNode {
    return $createImageNode(
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
    super(key);
    this.__src = src;
    this.__altText = altText;
    this.__caption = caption;
    this.__width = width;
    this.__height = height;
  }

  exportJSON(): SerializedImageNode {
    return {
      ...super.exportJSON(),
      type: 'lecture-image',
      src: this.__src,
      altText: this.__altText,
      caption: this.__caption,
      width: this.__width,
      height: this.__height,
      version: 1,
    };
  }

  createDOM(config: EditorConfig): HTMLElement {
    const div = document.createElement('div');
    div.className = 'lecture-image-wrapper my-4';
    div.setAttribute('data-lexical-key', this.__key);
    return div;
  }

  updateDOM(): false {
    return false;
  }

  // Getters
  getSrc(): string {
    return this.getLatest().__src;
  }

  getAltText(): string {
    return this.getLatest().__altText;
  }

  getCaption(): string {
    return this.getLatest().__caption;
  }

  getWidth(): ImageDimension {
    return this.getLatest().__width;
  }

  getHeight(): ImageDimension {
    return this.getLatest().__height;
  }

  getDimensions(): { width: ImageDimension; height: ImageDimension } {
    const latest = this.getLatest();
    return { width: latest.__width, height: latest.__height };
  }

  // Setters
  setSrc(src: string): this {
    const writable = this.getWritable();
    writable.__src = src;
    return writable;
  }

  setAltText(altText: string): this {
    const writable = this.getWritable();
    writable.__altText = altText;
    return writable;
  }

  setCaption(caption: string): this {
    const writable = this.getWritable();
    writable.__caption = caption;
    return writable;
  }

  setDimensions(width: ImageDimension, height: ImageDimension): this {
    const writable = this.getWritable();
    writable.__width = width;
    writable.__height = height;
    return writable;
  }

  setWidth(width: ImageDimension): this {
    const writable = this.getWritable();
    writable.__width = width;
    return writable;
  }

  setHeight(height: ImageDimension): this {
    const writable = this.getWritable();
    writable.__height = height;
    return writable;
  }

  decorate(_editor: LexicalEditor, config: EditorConfig): JSX.Element {
    // Динамический импорт компонента
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { ImageComponent } = require('../ImageComponent');
    return createElement(ImageComponent, {
      nodeKey: this.__key,
      src: this.__src,
      altText: this.__altText,
      caption: this.__caption,
      width: this.__width,
      height: this.__height,
    });
  }
}

export function $createImageNode(
  src: string,
  altText: string = '',
  caption: string = '',
  width: ImageDimension = 'auto',
  height: ImageDimension = 'auto'
): ImageNode {
  return $applyNodeReplacement(new ImageNode(src, altText, caption, width, height));
}

export function $isImageNode(
  node: LexicalNode | null | undefined
): node is ImageNode {
  return node instanceof ImageNode;
}
