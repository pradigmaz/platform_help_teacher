'use client';

import { useCallback, useState, useEffect, useRef } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import { $getNodeByKey, type NodeKey } from 'lexical';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTheme } from 'next-themes';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Code, Play, Copy, Check, ChevronDown, ChevronRight } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { 
  $isCodeBlockNode, 
  type CodeLanguage, 
  type RenderMode 
} from './nodes/CodeBlockNode';
import { VisualizationSandbox } from './VisualizationSandbox';

interface CodeBlockComponentProps {
  nodeKey: NodeKey;
  code: string;
  language: CodeLanguage;
  renderMode: RenderMode;
  hideCodeForStudents?: boolean;
  collapsed?: boolean;
  caption?: string;
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

export function CodeBlockComponent({
  nodeKey,
  code,
  language,
  renderMode,
  hideCodeForStudents = false,
  collapsed = false,
  caption = '',
}: CodeBlockComponentProps) {
  const [editor] = useLexicalComposerContext();
  const { resolvedTheme } = useTheme();
  const [copied, setCopied] = useState(false);
  const [localCode, setLocalCode] = useState(code);
  const [localCollapsed, setLocalCollapsed] = useState(collapsed);
  const [localCaption, setLocalCaption] = useState(caption);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const isDark = resolvedTheme === 'dark';
  const isRenderable = language === 'javascript' || language === 'typescript';


  // Sync local code with node
  useEffect(() => {
    setLocalCode(code);
  }, [code]);

  // Sync collapsed with node
  useEffect(() => {
    setLocalCollapsed(collapsed);
  }, [collapsed]);

  // Sync caption with node
  useEffect(() => {
    setLocalCaption(caption);
  }, [caption]);

  const updateCode = useCallback((newCode: string) => {
    setLocalCode(newCode);
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isCodeBlockNode(node)) {
        node.setCode(newCode);
      }
    });
  }, [editor, nodeKey]);

  const updateLanguage = useCallback((newLanguage: CodeLanguage) => {
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isCodeBlockNode(node)) {
        node.setLanguage(newLanguage);
      }
    });
  }, [editor, nodeKey]);

  const toggleRenderMode = useCallback(() => {
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isCodeBlockNode(node)) {
        node.toggleRenderMode();
      }
    });
  }, [editor, nodeKey]);

  const toggleCollapsed = useCallback(() => {
    setLocalCollapsed(prev => !prev);
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isCodeBlockNode(node)) {
        node.toggleCollapsed();
      }
    });
  }, [editor, nodeKey]);

  const updateCaption = useCallback((newCaption: string) => {
    setLocalCaption(newCaption);
    editor.update(() => {
      const node = $getNodeByKey(nodeKey);
      if ($isCodeBlockNode(node)) {
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
    <div className="my-4 rounded-lg border border-border bg-card text-card-foreground overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-muted/40">
        <div className="flex items-center gap-2">
          {/* Collapse toggle */}
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={toggleCollapsed}
          >
            {localCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
          
          <Code className="h-4 w-4 text-muted-foreground" />
          <Select value={language} onValueChange={(v) => updateLanguage(v as CodeLanguage)}>
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
        
        <div className="flex items-center gap-1">
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
          
          {isRenderable && (
            <Button
              variant={renderMode === 'render' ? 'default' : 'ghost'}
              size="sm"
              className="h-7 px-2 gap-1"
              onClick={toggleRenderMode}
            >
              <Play className="h-3.5 w-3.5" />
              <span className="text-xs">Run</span>
            </Button>
          )}
        </div>
      </div>


      {/* Content - collapsible */}
      {!localCollapsed && (
        <>
          {isRenderable ? (
            <Tabs value={renderMode} onValueChange={(v) => {
              if (v !== renderMode) toggleRenderMode();
            }}>
              <TabsList className="w-full justify-start rounded-none border-b bg-transparent h-9 px-2">
                <TabsTrigger value="code" className="text-xs data-[state=active]:bg-background">
                  Код
                </TabsTrigger>
                <TabsTrigger value="render" className="text-xs data-[state=active]:bg-background">
                  Результат
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="code" className="mt-0">
                <CodeEditor
                  code={localCode}
                  language={language}
                  isDark={isDark}
                  onChange={updateCode}
                  textareaRef={textareaRef}
                />
              </TabsContent>
              
              <TabsContent value="render" className="mt-0 min-h-[200px]">
                <VisualizationSandbox
                  code={localCode}
                  className="h-[300px]"
                  onError={(err) => console.error('Visualization error:', err)}
                />
              </TabsContent>
            </Tabs>
          ) : (
            <CodeEditor
              code={localCode}
              language={language}
              isDark={isDark}
              onChange={updateCode}
              textareaRef={textareaRef}
            />
          )}
        </>
      )}
      
      {/* Caption - как в Word: "Диаграмма 1 — Название" */}
      <figcaption className="py-2 px-3 border-t border-border">
        <Input
          value={localCaption}
          onChange={(e) => updateCaption(e.target.value)}
          placeholder="Диаграмма 1 — Описание..."
          className="text-center text-sm text-muted-foreground border-none bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0"
        />
      </figcaption>
    </div>
  );
}

interface CodeEditorProps {
  code: string;
  language: CodeLanguage;
  isDark: boolean;
  onChange: (code: string) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}

function CodeEditor({ code, language, isDark, onChange, textareaRef }: CodeEditorProps) {
  return (
    <div className="relative group bg-muted/20 max-h-[400px] overflow-auto">
      {/* Syntax highlighted display */}
      <SyntaxHighlighter
        language={PRISM_LANGUAGE_MAP[language]}
        style={isDark ? oneDark : oneLight}
        customStyle={{
          margin: 0,
          padding: '1rem',
          fontSize: '0.875rem',
          lineHeight: '1.5',
          background: 'transparent',
          minHeight: '100px',
        }}
        codeTagProps={{
          style: {
            fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
          }
        }}
      >
        {code || ' '}
      </SyntaxHighlighter>
      
      {/* Editable textarea overlay */}
      <textarea
        ref={textareaRef}
        value={code}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "absolute top-0 left-0 w-full min-h-full resize-none overflow-hidden",
          "p-4 font-mono text-sm leading-relaxed",
          "bg-transparent text-transparent caret-foreground",
          "focus:outline-none selection:bg-primary/30",
          "placeholder:text-muted-foreground"
        )}
        spellCheck={false}
        placeholder="// Введите код здесь..."
      />
    </div>
  );
}

export default CodeBlockComponent;
