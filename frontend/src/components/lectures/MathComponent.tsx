'use client';

import { useCallback, useState, useEffect, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getNodeByKey, type NodeKey } from 'lexical';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { cn } from '@/lib/utils';
import { $isMathNode } from './nodes/MathNode';

interface MathComponentProps {
  nodeKey: NodeKey;
  latex: string;
  displayMode: boolean;
}

export function MathComponent({ nodeKey, latex, displayMode }: MathComponentProps) {
  const [editor] = useLexicalComposerContext();
  const [isEditing, setIsEditing] = useState(false);
  const [localLatex, setLocalLatex] = useState(latex);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setLocalLatex(latex);
  }, [latex]);

  // Рендерим KaTeX
  useEffect(() => {
    if (isEditing || !containerRef.current) return;
    
    try {
      katex.render(localLatex, containerRef.current, {
        displayMode,
        throwOnError: false,
        errorColor: '#ef4444',
        trust: false,
        strict: 'warn',
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка рендеринга формулы');
    }
  }, [localLatex, displayMode, isEditing]);

  const handleSave = useCallback(() => {
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isMathNode(node)) {
        node.setLatex(localLatex);
      }
    });
    setIsEditing(false);
  }, [editor, nodeKey, localLatex]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSave();
    }
    if (e.key === 'Escape') {
      setLocalLatex(latex);
      setIsEditing(false);
    }
  }, [handleSave, latex]);

  // Фокус на input при редактировании
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  if (isEditing) {
    return (
      <div className={cn(
        "relative border rounded-md bg-muted/50",
        displayMode ? "my-4 p-3" : "inline-block px-2 py-1"
      )}>
        <textarea
          ref={inputRef}
          value={localLatex}
          onChange={(e) => setLocalLatex(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleSave}
          className={cn(
            "w-full bg-transparent font-mono text-sm resize-none focus:outline-none",
            displayMode ? "min-h-[60px]" : "min-h-[24px]"
          )}
          placeholder="LaTeX формула..."
        />
        <div className="text-xs text-muted-foreground mt-1">
          Ctrl+Enter — сохранить, Esc — отмена
        </div>
      </div>
    );
  }

  return (
    <span
      ref={containerRef}
      onClick={() => setIsEditing(true)}
      className={cn(
        "cursor-pointer hover:bg-muted/50 rounded transition-colors",
        displayMode ? "block my-4 py-2 text-center" : "inline px-0.5",
        error && "text-destructive"
      )}
      title={error || "Клик для редактирования"}
    />
  );
}

export default MathComponent;
