'use client';

import { useState, useCallback } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTheme } from 'next-themes';
import { Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type CodeLanguage = 
  | 'javascript' 
  | 'typescript' 
  | 'python' 
  | 'html' 
  | 'css' 
  | 'sql'
  | 'json'
  | 'bash'
  | 'plaintext';

const PRISM_LANGUAGE_MAP: Record<CodeLanguage, string> = {
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

const LANGUAGE_LABELS: Record<CodeLanguage, string> = {
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

interface CodeSnippetProps {
  code: string;
  language?: CodeLanguage;
  showLineNumbers?: boolean;
  showCopyButton?: boolean;
  caption?: string;
  className?: string;
}

export function CodeSnippet({
  code,
  language = 'javascript',
  showLineNumbers = true,
  showCopyButton = true,
  caption,
  className,
}: CodeSnippetProps) {
  const { resolvedTheme } = useTheme();
  const [copied, setCopied] = useState(false);
  const isDark = resolvedTheme === 'dark';

  const copyToClipboard = useCallback(async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [code]);

  return (
    <figure className={cn("my-4 rounded-lg border border-border overflow-hidden", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-muted/40">
        <span className="text-xs text-muted-foreground font-medium">
          {LANGUAGE_LABELS[language]}
        </span>
        {showCopyButton && (
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
        )}
      </div>

      {/* Code */}
      <div className="overflow-auto">
        <SyntaxHighlighter
          language={PRISM_LANGUAGE_MAP[language]}
          style={isDark ? oneDark : oneLight}
          showLineNumbers={showLineNumbers}
          customStyle={{
            margin: 0,
            padding: '1rem',
            fontSize: '0.875rem',
            lineHeight: '1.6',
            background: 'transparent',
          }}
          codeTagProps={{
            style: {
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
            }
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>

      {/* Caption */}
      {caption && (
        <figcaption className="py-2 px-3 border-t border-border text-center text-sm text-muted-foreground">
          {caption}
        </figcaption>
      )}
    </figure>
  );
}

export default CodeSnippet;
