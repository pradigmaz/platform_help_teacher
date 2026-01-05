'use client';

import { useMemo } from 'react';
import {
  InitialConfigType,
  LexicalComposer,
} from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { LexicalErrorBoundary } from '@lexical/react/LexicalErrorBoundary';
import type { SerializedEditorState } from 'lexical';
import { HeadingNode, QuoteNode } from '@lexical/rich-text';
import { ListNode, ListItemNode } from '@lexical/list';
import { LinkNode } from '@lexical/link';
import { ContentEditable } from '@/components/editor/editor-ui/content-editable';
import { editorTheme } from '@/components/editor/themes/editor-theme';
import { cn } from '@/lib/utils';
import { ViewerCodeBlockNode } from './nodes/ViewerCodeBlockNode';
import { ViewerImageNode } from './nodes/ViewerImageNode';
import { ViewerSnippetNode } from './nodes/ViewerSnippetNode';

// Custom nodes for viewer — native text nodes + viewer decorators
const viewerNodes = [
  HeadingNode,
  QuoteNode,
  ListNode,
  ListItemNode,
  LinkNode,
  ViewerCodeBlockNode,
  ViewerImageNode,
  ViewerSnippetNode,
];

// Дефолтное состояние с пустым параграфом
const defaultEditorState = {
  root: {
    children: [
      {
        type: 'paragraph',
        children: [],
        direction: null,
        format: '',
        indent: 0,
        version: 1,
      },
    ],
    direction: null,
    format: '',
    indent: 0,
    type: 'root',
    version: 1,
  },
} as unknown as SerializedEditorState;

interface LectureViewerProps {
  content: SerializedEditorState;
  title?: string;
  className?: string;
}

// Проверка валидности контента
function isValidContent(content: SerializedEditorState | undefined | null): boolean {
  if (!content) return false;
  if (!content.root) return false;
  if (!content.root.children || content.root.children.length === 0) return false;
  return true;
}

export function LectureViewer({
  content,
  title,
  className,
}: LectureViewerProps) {
  // Используем валидный контент или дефолт
  const validContent = isValidContent(content) ? content : defaultEditorState;
  
  // Stable hash for content key
  const contentKey = useMemo(() => {
    const str = JSON.stringify(validContent);
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return `viewer-${hash}`;
  }, [validContent]);

  const editorConfig: InitialConfigType = {
    namespace: 'LectureViewer',
    theme: {
      ...editorTheme,
      code: 'code-block-container',
      image: 'lecture-image-container',
    },
    nodes: viewerNodes,
    editable: false,
    onError: (error: Error) => {
      console.error('Lecture Viewer Error:', error);
    },
    editorState: JSON.stringify(validContent),
  };

  return (
    <article className={cn("bg-background", className)}>
      {title && (
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
            {title}
          </h1>
        </header>
      )}
      
      <LexicalComposer key={contentKey} initialConfig={editorConfig}>
        <div className="prose prose-neutral dark:prose-invert max-w-none">
          <RichTextPlugin
            contentEditable={
              <ContentEditable 
                placeholder="" 
                className="ContentEditable__root outline-none"
              />
            }
            ErrorBoundary={LexicalErrorBoundary}
          />
        </div>
      </LexicalComposer>
    </article>
  );
}

export default LectureViewer;
