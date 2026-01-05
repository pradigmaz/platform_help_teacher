'use client';

import { useCallback, useState, useEffect, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getNodeByKey, type NodeKey } from 'lexical';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Copy, Check, FileCode2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { $isSnippetNode, type SnippetLanguage } from './nodes/SnippetNode';

interface SnippetComponentProps {
  nodeKey: NodeKey;
  code: string;
  language: SnippetLanguage;
  caption: string;
  showLineNumbers: boolean;
}

const LANGUAGE_LABELS: Record<SnippetLanguage, string> = {
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  python: 'Python',
  html: 'HTML',
  css: 'CSS',
  sql: 'SQL',
  json: 'JSON',
  bash: 'Bash',
  plaintext: 'Text',
};

const PRISM_LANGUAGE_MAP: Record<SnippetLanguage, string> = {
  javascript: 'javascript',
  typescript: 'typescript',
  python: 'python',
  html: 'markup',
  css: 'css',
  sql: 'sql',
  json: 'json',
  bash: 'bash',
  plaintext: 'text',
};

export function SnippetComponent({
  nodeKey,
  code,
  language,
  caption,
  showLineNumbers,
}: SnippetComponentProps) {
  const [editor] = useLexicalComposerContext();
  const { resolvedTheme } = useTheme();
  const [copied, setCopied] = useState(false);
  const [localCode, setLocalCode] = useState(code);
  const [localCaption, setLocalCaption] = useState(caption);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const isDark = resolvedTheme === 'dark';

  useEffect(() => {
    setLocalCode(code);
  }, [code]);

  useEffect(() => {
    setLocalCaption(caption);
  }, [caption]);

  const updateCode = useCallback((newCode: string) => {
    setLocalCode(newCode);
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isSnippetNode(node)) {
        node.setCode(newCode);
      }
    });
  }, [editor, nodeKey]);

  const updateLanguage = useCallback((newLanguage: SnippetLanguage) => {
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isSnippetNode(node)) {
        node.setLanguage(newLanguage);
      }
    });
  }, [editor, nodeKey]);

  const updateCaption = useCallback((newCaption: string) => {
    setLocalCaption(newCaption);
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isSnippetNode(node)) {
        node.setCaption(newCaption);
      }
    });
  }, [editor, nodeKey]);

  const copyToClipboard = useCallback(async () => {
    await navigator.clipboard.writeText(localCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [localCode]);

  return (
    <figure className="my-4 rounded-lg border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-muted/40">
        <div className="flex items-center gap-2">
          <FileCode2 className="h-4 w-4 text-muted-foreground" />
          <Select value={language} onValueChange={(v) => updateLanguage(v as SnippetLanguage)}>
            <SelectTrigger className="h-7 w-[130px] text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(LANGUAGE_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value} className="text-xs">
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2"
          onClick={copyToClipboard}
        >
          {copied ? (
            <Check className="h-3.5 w-3.5 text-green-500" />
          ) : (
            <Copy className="h-3.5 w-3.5" />
          )}
        </Button>
      </div>

      {/* Code editor */}
      <div className="relative group bg-muted/20 max-h-[400px] overflow-auto">
        <SyntaxHighlighter
          language={PRISM_LANGUAGE_MAP[language]}
          style={isDark ? oneDark : oneLight}
          showLineNumbers={showLineNumbers}
          customStyle={{
            margin: 0,
            padding: '1rem',
            fontSize: '0.875rem',
            lineHeight: '1.5',
            background: 'transparent',
            minHeight: '80px',
          }}
          codeTagProps={{
            style: {
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
            }
          }}
        >
          {localCode || ' '}
        </SyntaxHighlighter>
        
        <textarea
          ref={textareaRef}
          value={localCode}
          onChange={(e) => updateCode(e.target.value)}
          className={cn(
            "absolute top-0 left-0 w-full min-h-full resize-none overflow-hidden",
            "p-4 font-mono text-sm leading-relaxed",
            "bg-transparent text-transparent caret-foreground",
            "focus:outline-none selection:bg-primary/30",
            "placeholder:text-muted-foreground"
          )}
          style={{ paddingLeft: showLineNumbers ? '3.5rem' : '1rem' }}
          spellCheck={false}
          placeholder="// Введите код..."
        />
      </div>

      {/* Caption */}
      <figcaption className="py-2 px-3 border-t border-border">
        <Input
          value={localCaption}
          onChange={(e) => updateCaption(e.target.value)}
          placeholder="Листинг 1 — Описание кода..."
          className="text-center text-sm text-muted-foreground border-none bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0"
        />
      </figcaption>
    </figure>
  );
}

export default SnippetComponent;
