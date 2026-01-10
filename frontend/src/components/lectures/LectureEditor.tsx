'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { InitialConfigType, LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { LexicalErrorBoundary } from '@lexical/react/LexicalErrorBoundary';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { EditorState, SerializedEditorState } from 'lexical';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ContentEditable } from '@/components/editor/editor-ui/content-editable';
import { editorTheme } from '@/components/editor/themes/editor-theme';
import { cn } from '@/lib/utils';
import { EditorToolbar } from './EditorToolbar';
import { CodeBlockNode } from './nodes/CodeBlockNode';
import { ImageNode } from './nodes/ImageNode';
import { SnippetNode } from './nodes/SnippetNode';
import { MarkdownPastePlugin } from './plugins/MarkdownPastePlugin';
import { Badge } from '@/components/ui/badge';
import { Cloud, CloudOff, Loader2 } from 'lucide-react';
import { HeadingNode, QuoteNode } from '@lexical/rich-text';
import { ListNode, ListItemNode } from '@lexical/list';
import { LinkNode } from '@lexical/link';
import { ListPlugin } from '@lexical/react/LexicalListPlugin';
import { MarkdownShortcutPlugin } from '@lexical/react/LexicalMarkdownShortcutPlugin';
import { 
  BOLD_ITALIC_STAR, BOLD_ITALIC_UNDERSCORE, BOLD_STAR, BOLD_UNDERSCORE, 
  ITALIC_STAR, ITALIC_UNDERSCORE, STRIKETHROUGH, HEADING, QUOTE, 
  UNORDERED_LIST, ORDERED_LIST,
} from '@lexical/markdown';
import { ToolbarPreset, getPresetConfig } from './presets';

const LECTURE_TRANSFORMERS = [
  HEADING, QUOTE, UNORDERED_LIST, ORDERED_LIST,
  BOLD_ITALIC_STAR, BOLD_ITALIC_UNDERSCORE, BOLD_STAR, BOLD_UNDERSCORE,
  ITALIC_STAR, ITALIC_UNDERSCORE, STRIKETHROUGH,
];

const lectureNodes = [
  HeadingNode, QuoteNode, ListNode, ListItemNode, LinkNode,
  CodeBlockNode, ImageNode, SnippetNode,
];

interface LectureEditorProps {
  initialContent?: SerializedEditorState;
  onSave?: (content: SerializedEditorState) => Promise<void>;
  onChange?: (content: SerializedEditorState) => void;
  autoSaveInterval?: number;
  className?: string;
  readOnly?: boolean;
  placeholder?: string;
  preset?: ToolbarPreset;
  // Внешние стили (для синхронизации между редакторами)
  externalFontSize?: string;
  externalLineHeight?: string;
  onFontSizeChange?: (size: string) => void;
  onLineHeightChange?: (height: string) => void;
}

function AutoSavePlugin({ onSave, interval = 30000 }: { onSave: (content: SerializedEditorState) => Promise<void>; interval?: number }) {
  const [editor] = useLexicalComposerContext();
  const lastSavedRef = useRef<string>('');
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const saveContent = async () => {
      const json = editor.getEditorState().toJSON();
      const jsonString = JSON.stringify(json);
      if (jsonString !== lastSavedRef.current) {
        await onSave(json);
        lastSavedRef.current = jsonString;
      }
    };
    timeoutRef.current = setInterval(saveContent, interval);
    return () => { if (timeoutRef.current) clearInterval(timeoutRef.current); };
  }, [editor, onSave, interval]);

  return null;
}

function KeyboardShortcutsPlugin({ onSave }: { onSave: () => void }) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); onSave(); }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onSave]);
  return null;
}

export function LectureEditor({
  initialContent,
  onSave,
  onChange,
  autoSaveInterval = 30000,
  className,
  readOnly = false,
  placeholder = 'Начните писать...',
  preset = 'full',
  externalFontSize,
  externalLineHeight,
  onFontSizeChange,
  onLineHeightChange,
}: LectureEditorProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'error' | 'idle'>('idle');
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const editorStateRef = useRef<SerializedEditorState | null>(null);

  const config = getPresetConfig(preset);
  const showStatusBar = preset === 'full';

  const defaultEditorState = {
    root: {
      children: [{ type: 'paragraph', children: [], direction: null, format: '', indent: 0, version: 1 }],
      direction: null, format: '', indent: 0, type: 'root', version: 1,
    },
  } as unknown as SerializedEditorState;

  const isValidContent = (content: SerializedEditorState | undefined): boolean => {
    return !!(content?.root?.children?.length);
  };

  const editorState = isValidContent(initialContent) ? initialContent : defaultEditorState;

  const editorConfig: InitialConfigType = {
    namespace: 'LectureEditor',
    theme: { ...editorTheme, code: 'code-block-container', image: 'lecture-image-container' },
    nodes: lectureNodes,
    editable: !readOnly,
    onError: (error: Error) => console.error('Lecture Editor Error:', error),
    editorState: JSON.stringify(editorState),
  };

  const handleSave = useCallback(async () => {
    if (!onSave || !editorStateRef.current) return;
    setIsSaving(true);
    setSaveStatus('saving');
    try {
      await onSave(editorStateRef.current);
      setSaveStatus('saved');
      setLastSaved(new Date());
    } catch (error) {
      console.error('Save error:', error);
      setSaveStatus('error');
    } finally {
      setIsSaving(false);
    }
  }, [onSave]);

  const handleAutoSave = useCallback(async (content: SerializedEditorState) => {
    if (!onSave) return;
    setSaveStatus('saving');
    try {
      await onSave(content);
      setSaveStatus('saved');
      setLastSaved(new Date());
    } catch (error) {
      console.error('Auto-save error:', error);
      setSaveStatus('error');
    }
  }, [onSave]);

  const handleChange = useCallback((editorState: EditorState) => {
    const json = editorState.toJSON();
    editorStateRef.current = json;
    onChange?.(json);
  }, [onChange]);

  const showToolbar = !readOnly && preset !== 'none';

  return (
    <div className={cn("bg-background text-foreground overflow-hidden rounded-lg border shadow", className)}>
      <LexicalComposer initialConfig={editorConfig}>
        <TooltipProvider>
          {showToolbar && (
            <EditorToolbar 
              onSave={config.showSave && onSave ? handleSave : undefined} 
              isSaving={isSaving} 
              config={config}
              onFontSizeChange={onFontSizeChange}
              onLineHeightChange={onLineHeightChange}
            />
          )}

          {showStatusBar && (
            <div className="flex items-center justify-between px-3 py-1.5 border-b bg-muted/30 text-xs text-muted-foreground">
              <div className="flex items-center gap-2">
                {saveStatus === 'saving' && <Badge variant="secondary" className="gap-1 text-xs"><Loader2 className="h-3 w-3 animate-spin" />Сохранение...</Badge>}
                {saveStatus === 'saved' && <Badge variant="secondary" className="gap-1 text-xs text-green-600 dark:text-green-400"><Cloud className="h-3 w-3" />Сохранено</Badge>}
                {saveStatus === 'error' && <Badge variant="destructive" className="gap-1 text-xs"><CloudOff className="h-3 w-3" />Ошибка</Badge>}
              </div>
              {lastSaved && <span>Сохранено: {lastSaved.toLocaleTimeString()}</span>}
            </div>
          )}

          <div 
            className="relative bg-background" 
            style={{ 
              minHeight: config.minHeight,
              fontSize: externalFontSize ? `${externalFontSize}px` : undefined,
              lineHeight: externalLineHeight || undefined,
            }}
          >
            <RichTextPlugin
              contentEditable={
                <ContentEditable 
                  placeholder={readOnly ? '' : placeholder} 
                  className={cn("ContentEditable__root relative block overflow-auto focus:outline-none text-foreground", config.padding)}
                  placeholderClassName="text-muted-foreground/40 pointer-events-none absolute top-2 left-3 overflow-hidden text-ellipsis select-none"
                />
              }
              ErrorBoundary={LexicalErrorBoundary}
            />
            <HistoryPlugin />
            <ListPlugin />
            <OnChangePlugin ignoreSelectionChange={true} onChange={handleChange} />
            {onSave && !readOnly && <AutoSavePlugin onSave={handleAutoSave} interval={autoSaveInterval} />}
            {onSave && !readOnly && <KeyboardShortcutsPlugin onSave={handleSave} />}
            {!readOnly && <MarkdownPastePlugin />}
            {!readOnly && <MarkdownShortcutPlugin transformers={LECTURE_TRANSFORMERS} />}
          </div>
        </TooltipProvider>
      </LexicalComposer>
    </div>
  );
}

export default LectureEditor;
