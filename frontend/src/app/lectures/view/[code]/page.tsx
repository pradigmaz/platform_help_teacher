'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { motion } from 'motion/react';
import { Loader2, AlertCircle, BookOpen, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { LectureViewer } from '@/components/lectures/LectureViewer';
import { PublicLecturesAPI, type LectureResponse } from '@/lib/lectures-api';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  LecturePublicHeader,
  LecturePublicTOC,
  type ReaderSettings,
  type TOCItem,
} from '@/components/lectures/public';

type LoadingState = 'loading' | 'success' | 'error' | 'not_found';

const DEFAULT_SETTINGS: ReaderSettings = {
  theme: 'light',
  fontFamily: 'sans',
  fontSize: 18,
};

export default function PublicLecturePage() {
  const params = useParams();
  const code = params.code as string;
  
  const [lecture, setLecture] = useState<LectureResponse | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [settings, setSettings] = useState<ReaderSettings>(DEFAULT_SETTINGS);
  const [progress, setProgress] = useState(0);
  const [activeHeadingId, setActiveHeadingId] = useState('');
  const [tocItems, setTocItems] = useState<TOCItem[]>([]);

  // Load settings from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('lecture-reader-settings');
    if (saved) {
      try {
        setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(saved) });
      } catch {}
    }
  }, []);

  // Save settings to localStorage
  const updateSettings = useCallback((newSettings: Partial<ReaderSettings>) => {
    setSettings(prev => {
      const updated = { ...prev, ...newSettings };
      localStorage.setItem('lecture-reader-settings', JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('light', 'dark', 'sepia');
    if (settings.theme !== 'light') {
      root.classList.add(settings.theme);
    }
  }, [settings.theme]);

  // Scroll progress
  useEffect(() => {
    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollProgress = (window.scrollY / totalHeight) * 100;
      setProgress(Math.min(100, Math.max(0, scrollProgress)));
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Extract TOC from content
  useEffect(() => {
    if (loadingState !== 'success' || !lecture) return;

    // Extract headings from Lexical content
    const items: TOCItem[] = [];
    
    const extractHeadings = (nodes: unknown[]) => {
      for (const node of nodes) {
        const n = node as { type?: string; tag?: string; children?: unknown[]; text?: string };
        if (n.type === 'heading' && n.tag) {
          const level = parseInt(n.tag.replace('h', ''));
          const text = extractText(n.children || []);
          if (text) {
            const id = text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
            items.push({ id, text, level });
          }
        }
        if (n.children) {
          extractHeadings(n.children);
        }
      }
    };

    const extractText = (nodes: unknown[]): string => {
      return nodes.map(n => {
        const node = n as { text?: string; children?: unknown[] };
        if (node.text) return node.text;
        if (node.children) return extractText(node.children);
        return '';
      }).join('');
    };

    const content = lecture.content as { root?: { children?: unknown[] } };
    if (content.root?.children) {
      extractHeadings(content.root.children);
    }
    
    setTocItems(items);

    // Add IDs to rendered headings after a short delay
    setTimeout(() => {
      const headings = document.querySelectorAll('.lecture-content h1, .lecture-content h2, .lecture-content h3');
      headings.forEach((heading, index) => {
        if (items[index]) {
          heading.id = items[index].id;
        }
      });
    }, 100);
  }, [loadingState, lecture]);

  // Observe headings for active state
  useEffect(() => {
    if (tocItems.length === 0) return;

    let observer: IntersectionObserver | null = null;
    const visibleHeadings = new Set<string>();

    // Delay to ensure IDs are set
    const timeoutId = setTimeout(() => {
      const headings = tocItems
        .map(item => document.getElementById(item.id))
        .filter((el): el is HTMLElement => el !== null);
      
      if (headings.length === 0) return;

      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              visibleHeadings.add(entry.target.id);
            } else {
              visibleHeadings.delete(entry.target.id);
            }
          });

          // Find the topmost visible heading based on TOC order
          for (const item of tocItems) {
            if (visibleHeadings.has(item.id)) {
              setActiveHeadingId(item.id);
              break;
            }
          }
        },
        { rootMargin: '-80px 0px -50% 0px', threshold: 0 }
      );

      headings.forEach((heading) => observer?.observe(heading));
    }, 300);

    return () => {
      clearTimeout(timeoutId);
      observer?.disconnect();
    };
  }, [tocItems]);

  // Fetch lecture
  useEffect(() => {
    if (!code) return;

    const fetchLecture = async () => {
      setLoadingState('loading');
      try {
        const data = await PublicLecturesAPI.getByCode(code);
        setLecture(data);
        setLoadingState('success');
      } catch (error: unknown) {
        console.error('Failed to fetch lecture:', error);
        if (error && typeof error === 'object' && 'response' in error) {
          const axiosError = error as { response?: { status?: number } };
          if (axiosError.response?.status === 404) {
            setLoadingState('not_found');
            return;
          }
        }
        setErrorMessage('Не удалось загрузить лекцию');
        setLoadingState('error');
      }
    };

    fetchLecture();
  }, [code]);

  const scrollToHeading = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el) {
      const offset = 80;
      const top = el.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  }, []);

  // Theme classes - use CSS variables only
  const getFontClass = () => {
    switch (settings.fontFamily) {
      case 'serif': return 'font-serif';
      case 'mono': return 'font-mono';
      default: return 'font-sans';
    }
  };

  // Loading state
  if (loadingState === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Загрузка лекции...</p>
        </motion.div>
      </div>
    );
  }

  // Not found state
  if (loadingState === 'not_found') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center gap-6 text-center max-w-md px-4"
        >
          <div className="p-4 rounded-full bg-muted">
            <BookOpen className="h-12 w-12 text-muted-foreground" />
          </div>
          <div>
            <h1 className="text-2xl font-bold mb-2">Лекция не найдена</h1>
            <p className="text-muted-foreground">
              Возможно, ссылка устарела или лекция была удалена.
            </p>
          </div>
          <Link href="/">
            <Button variant="outline" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              На главную
            </Button>
          </Link>
        </motion.div>
      </div>
    );
  }

  // Error state
  if (loadingState === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center gap-6 text-center max-w-md px-4"
        >
          <div className="p-4 rounded-full bg-destructive/10">
            <AlertCircle className="h-12 w-12 text-destructive" />
          </div>
          <div>
            <h1 className="text-2xl font-bold mb-2">Ошибка загрузки</h1>
            <p className="text-muted-foreground">{errorMessage}</p>
          </div>
          <Button 
            variant="outline" 
            onClick={() => window.location.reload()}
            className="gap-2"
          >
            Попробовать снова
          </Button>
        </motion.div>
      </div>
    );
  }

  if (!lecture) return null;

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      <LecturePublicHeader
        title={lecture.title}
        progress={progress}
        settings={settings}
        onUpdateSettings={updateSettings}
      />

      <div className="pt-20 pb-16 px-4 max-w-7xl mx-auto flex">
        {/* TOC Sidebar - Desktop */}
        <aside className="hidden lg:block w-64 flex-shrink-0 mr-8">
          <div className="sticky top-20">
            <LecturePublicTOC
              items={tocItems}
              activeId={activeHeadingId}
              onItemClick={scrollToHeading}
            />
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0 max-w-4xl">
          <motion.article
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className={getFontClass()}
            style={{ fontSize: `${settings.fontSize}px` }}
          >
            <header className="mb-10 pb-8 border-b border-border">
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
                {lecture.title}
              </h1>
            </header>

            <div className="lecture-content" style={{ lineHeight: '1.7' }}>
              <LectureViewer
                content={lecture.content}
                className="max-w-none"
              />
            </div>
          </motion.article>
        </main>
      </div>
    </div>
  );
}
