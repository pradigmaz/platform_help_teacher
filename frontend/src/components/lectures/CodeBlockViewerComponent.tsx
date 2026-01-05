'use client';

import { useState, useCallback } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTheme } from 'next-themes';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Code, Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { VisualizationSandbox } from './VisualizationSandbox';
import type { CodeLanguage, RenderMode } from './nodes/CodeBlockNode';

interface CodeBlockViewerComponentProps {
  code: string;
  language: CodeLanguage;
  renderMode: RenderMode;
  hideCodeForStudents?: boolean;
}

const LANGUAGE_LABELS: Record<CodeLanguage, string> = {
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  python: 'Python',
  html: 'HTML',
  css: 'CSS',
  sql: 'SQL',
};

const PRISM_LANGUAGE_MAP: Record<CodeLanguage, string> = {
  javascript: 'javascript',
  typescript: 'typescript',
  python: 'python',
  html: 'markup',
  css: 'css',
  sql: 'sql',
};

export function CodeBlockViewerComponent({
  code,
  language,
  renderMode,
  hideCodeForStudents = false,
}: CodeBlockViewerComponentProps) {
  const { resolvedTheme } = useTheme();
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<RenderMode>(renderMode);
  
  const isDark = resolvedTheme === 'dark';
  const isRenderable = language === 'javascript' || language === 'typescript';

  const copyToClipboard = useCallback(async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [code]);

  // Если hideCodeForStudents=true и код можно рендерить — показываем только визуализацию
  if (hideCodeForStudents && isRenderable) {
    return (
      <div className="my-4 rounded-lg border bg-card overflow-hidden">
        <VisualizationSandbox
          code={code}
          className="h-[300px]"
          onError={(err) => console.error('Visualization error:', err)}
        />
      </div>
    );
  }

  return (
    <div className="my-4 rounded-lg border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b bg-muted/50">
        <div className="flex items-center gap-2">
          <Code className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs font-medium text-muted-foreground">
            {LANGUAGE_LABELS[language]}
          </span>
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

      {/* Content */}
      {isRenderable ? (
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as RenderMode)}>
          <TabsList className="w-full justify-start rounded-none border-b bg-transparent h-9 px-2">
            <TabsTrigger value="code" className="text-xs data-[state=active]:bg-background">
              Код
            </TabsTrigger>
            <TabsTrigger value="render" className="text-xs data-[state=active]:bg-background">
              Результат
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="code" className="mt-0">
            <CodeDisplay code={code} language={language} isDark={isDark} />
          </TabsContent>
          
          <TabsContent value="render" className="mt-0 min-h-[200px]">
            <VisualizationSandbox
              code={code}
              className="h-[300px]"
              onError={(err) => console.error('Visualization error:', err)}
            />
          </TabsContent>
        </Tabs>
      ) : (
        <CodeDisplay code={code} language={language} isDark={isDark} />
      )}
    </div>
  );
}

interface CodeDisplayProps {
  code: string;
  language: CodeLanguage;
  isDark: boolean;
}

function CodeDisplay({ code, language, isDark }: CodeDisplayProps) {
  return (
    <SyntaxHighlighter
      language={PRISM_LANGUAGE_MAP[language]}
      style={isDark ? oneDark : oneLight}
      customStyle={{
        margin: 0,
        padding: '1rem',
        fontSize: '0.875rem',
        lineHeight: '1.5',
        background: 'transparent',
        minHeight: '60px',
      }}
      codeTagProps={{
        style: {
          fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
        }
      }}
    >
      {code || ' '}
    </SyntaxHighlighter>
  );
}

export default CodeBlockViewerComponent;
