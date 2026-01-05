'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { AlertCircle, RefreshCw, Loader2, Camera } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface VisualizationSandboxProps {
  code: string;
  className?: string;
  onError?: (error: string) => void;
  onReady?: () => void;
  onSnapshot?: (blob: Blob) => void;
}

type SandboxStatus = 'idle' | 'loading' | 'ready' | 'error';

// CDN URLs for libraries
const LIBRARY_URLS = {
  Chart: 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js',
  THREE: 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js',
  Plotly: 'https://cdn.plot.ly/plotly-2.27.0.min.js',
};

// Cache for fetched library source code
let librarySourceCache: Record<string, string> | null = null;

async function fetchLibrarySources(): Promise<Record<string, string>> {
  if (librarySourceCache) return librarySourceCache;
  
  const entries = await Promise.all(
    Object.entries(LIBRARY_URLS).map(async ([name, url]) => {
      try {
        const res = await fetch(url);
        const code = await res.text();
        return [name, code] as const;
      } catch {
        console.warn(`Failed to fetch ${name}`);
        return [name, ''] as const;
      }
    })
  );
  
  librarySourceCache = Object.fromEntries(entries);
  return librarySourceCache;
}

// Sandbox HTML template - libraries injected inline
const createSandboxHTML = (isDark: boolean, libSources: Record<string, string>) => `
<!DOCTYPE html>
<html class="${isDark ? 'dark' : ''}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { 
      width: 100%; 
      height: 100%; 
      overflow: hidden;
      font-family: system-ui, -apple-system, sans-serif;
      background: ${isDark ? '#0a0a0a' : '#ffffff'};
      color: ${isDark ? '#fafafa' : '#0a0a0a'};
    }
    #container { 
      width: 100%; 
      height: 100%; 
      display: flex;
      align-items: center;
      justify-content: center;
    }
    canvas { max-width: 100%; max-height: 100%; }
    .error { color: #ef4444; padding: 1rem; text-align: center; font-size: 0.875rem; }
    .loading { color: ${isDark ? '#a1a1aa' : '#71717a'}; font-size: 0.875rem; }
  </style>
</head>
<body>
  <div id="container"></div>
  <script>${libSources.Chart || ''}</script>
  <script>${libSources.THREE || ''}</script>
  <script>${libSources.Plotly || ''}</script>
  <script>
    const container = document.getElementById('container');
    
    window.addEventListener('message', async (event) => {
      if (event.data.type === 'execute') {
        try {
          container.innerHTML = '';
          
          const safeGlobals = {
            container,
            Chart: window.Chart,
            THREE: window.THREE,
            Plotly: window.Plotly,
            console: {
              log: (...args) => parent.postMessage({ type: 'log', args }, '*'),
              error: (...args) => parent.postMessage({ type: 'log', args, level: 'error' }, '*'),
              warn: (...args) => parent.postMessage({ type: 'log', args, level: 'warn' }, '*'),
            },
            requestAnimationFrame: window.requestAnimationFrame.bind(window),
            cancelAnimationFrame: window.cancelAnimationFrame.bind(window),
            setTimeout: window.setTimeout.bind(window),
            clearTimeout: window.clearTimeout.bind(window),
          };
          
          const timeoutId = setTimeout(() => {
            throw new Error('Execution timeout (5s)');
          }, 5000);
          
          const fn = new Function(...Object.keys(safeGlobals), event.data.code);
          await fn(...Object.values(safeGlobals));
          
          clearTimeout(timeoutId);
          parent.postMessage({ type: 'ready' }, '*');
        } catch (error) {
          parent.postMessage({ type: 'error', message: error.message || 'Unknown error' }, '*');
        }
      }
    });
    
    parent.postMessage({ type: 'loaded' }, '*');
  </script>
</body>
</html>
`;

export function VisualizationSandbox({
  code,
  className,
  onError,
  onReady,
  onSnapshot,
}: VisualizationSandboxProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [status, setStatus] = useState<SandboxStatus>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [sandboxLoaded, setSandboxLoaded] = useState(false);
  const [sandboxUrl, setSandboxUrl] = useState<string | null>(null);
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  // Fetch libraries and create sandbox
  useEffect(() => {
    let cancelled = false;
    let url: string | null = null;
    
    (async () => {
      const libSources = await fetchLibrarySources();
      if (cancelled) return;
      
      const html = createSandboxHTML(isDark, libSources);
      const blob = new Blob([html], { type: 'text/html' });
      url = URL.createObjectURL(blob);
      setSandboxUrl(url);
      setSandboxLoaded(false);
    })();
    
    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [isDark]);

  // Handle messages from sandbox
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.source !== iframeRef.current?.contentWindow) return;

      switch (event.data.type) {
        case 'loaded':
          setSandboxLoaded(true);
          break;
        case 'ready':
          setStatus('ready');
          setErrorMessage(null);
          onReady?.();
          break;
        case 'error':
          setStatus('error');
          setErrorMessage(event.data.message);
          onError?.(event.data.message);
          break;
        case 'log':
          const level = event.data.level || 'log';
          console[level as 'log' | 'error' | 'warn']('[Sandbox]', ...event.data.args);
          break;
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onError, onReady]);

  // Execute code when sandbox is loaded
  useEffect(() => {
    if (!sandboxLoaded || !code.trim()) return;

    setStatus('loading');
    setErrorMessage(null);

    const timeoutId = setTimeout(() => {
      iframeRef.current?.contentWindow?.postMessage({ type: 'execute', code }, '*');
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [code, sandboxLoaded]);

  const handleRefresh = useCallback(() => {
    if (!code.trim()) return;
    setStatus('loading');
    setErrorMessage(null);
    iframeRef.current?.contentWindow?.postMessage({ type: 'execute', code }, '*');
  }, [code]);

  const handleSnapshot = useCallback(async () => {
    if (!iframeRef.current || status !== 'ready') return;
    try {
      const canvas = iframeRef.current.contentDocument?.querySelector('canvas');
      if (canvas) {
        canvas.toBlob((blob) => { if (blob) onSnapshot?.(blob); }, 'image/png');
      }
    } catch (error) {
      console.error('Failed to capture snapshot:', error);
    }
  }, [status, onSnapshot]);

  return (
    <div className={cn("relative", className)}>
      <iframe
        ref={iframeRef}
        src={sandboxUrl || undefined}
        sandbox="allow-scripts"
        className={cn(
          "w-full h-full border-0 rounded-lg bg-background",
          status === 'loading' && "opacity-50"
        )}
        title="Visualization Sandbox"
      />

      <AnimatePresence>
        {status === 'loading' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm rounded-lg"
          >
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <span className="text-sm text-muted-foreground">Выполнение...</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {status === 'error' && errorMessage && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute inset-0 flex items-center justify-center bg-destructive/10 backdrop-blur-sm rounded-lg p-4"
          >
            <div className="flex flex-col items-center gap-3 text-center max-w-md">
              <AlertCircle className="h-8 w-8 text-destructive" />
              <div>
                <p className="font-medium text-destructive">Ошибка выполнения</p>
                <p className="text-sm text-muted-foreground mt-1 font-mono">{errorMessage}</p>
              </div>
              <Button variant="outline" size="sm" onClick={handleRefresh} className="gap-2">
                <RefreshCw className="h-3.5 w-3.5" />
                Повторить
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {status === 'ready' && (
        <div className="absolute top-2 right-2 flex gap-1">
          <Button
            variant="secondary"
            size="sm"
            className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={handleRefresh}
            title="Перезапустить"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
          {onSnapshot && (
            <Button
              variant="secondary"
              size="sm"
              className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={handleSnapshot}
              title="Сделать снимок"
            >
              <Camera className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

export default VisualizationSandbox;
