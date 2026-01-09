'use client';
'use no memo';

import { useEffect, useState, useCallback } from 'react';
import { PublicLecturesAPI, type LectureResponse } from '@/lib/lectures-api';
import type { ReaderSettings, TOCItem } from './types';

type LoadingState = 'loading' | 'success' | 'error' | 'not_found';

const DEFAULT_SETTINGS: ReaderSettings = {
  theme: 'light',
  fontFamily: 'sans',
  fontSize: 18,
};

const SETTINGS_KEY = 'lecture-reader-settings';

interface UseLectureReaderResult {
  lecture: LectureResponse | null;
  loadingState: LoadingState;
  errorMessage: string;
  settings: ReaderSettings;
  updateSettings: (newSettings: Partial<ReaderSettings>) => void;
  progress: number;
  activeHeadingId: string;
  tocItems: TOCItem[];
  scrollToHeading: (id: string) => void;
  getFontClass: () => string;
}

/**
 * Hook for lecture reader state management
 */
export function useLectureReader(code: string): UseLectureReaderResult {
  const [lecture, setLecture] = useState<LectureResponse | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [settings, setSettings] = useState<ReaderSettings>(DEFAULT_SETTINGS);
  const [progress, setProgress] = useState(0);
  const [activeHeadingId, setActiveHeadingId] = useState('');
  const [tocItems, setTocItems] = useState<TOCItem[]>([]);

  // Load settings from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(SETTINGS_KEY);
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
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(updated));
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

  // Extract TOC from content
  useEffect(() => {
    if (loadingState !== 'success' || !lecture) return;

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

  const scrollToHeading = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el) {
      const offset = 80;
      const top = el.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  }, []);

  const getFontClass = useCallback(() => {
    switch (settings.fontFamily) {
      case 'serif': return 'font-serif';
      case 'mono': return 'font-mono';
      default: return 'font-sans';
    }
  }, [settings.fontFamily]);

  return {
    lecture,
    loadingState,
    errorMessage,
    settings,
    updateSettings,
    progress,
    activeHeadingId,
    tocItems,
    scrollToHeading,
    getFontClass,
  };
}
