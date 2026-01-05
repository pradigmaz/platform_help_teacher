'use client';

import { ArrowLeft, Sun, Moon, BookOpen } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { LecturePublicSettings } from './LecturePublicSettings';
import type { ReaderSettings, Theme } from './types';

interface Props {
  title: string;
  progress: number;
  settings: ReaderSettings;
  onUpdateSettings: (settings: Partial<ReaderSettings>) => void;
}

export function LecturePublicHeader({ title, progress, settings, onUpdateSettings }: Props) {
  const cycleTheme = () => {
    const themes: Theme[] = ['light', 'dark', 'sepia'];
    const currentIndex = themes.indexOf(settings.theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    onUpdateSettings({ theme: themes[nextIndex] });
  };

  const ThemeIcon = settings.theme === 'dark' ? Moon : settings.theme === 'sepia' ? BookOpen : Sun;

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/90 backdrop-blur-md border-b border-border transition-colors duration-300">
      {/* Progress bar */}
      <div 
        className="absolute bottom-0 left-0 h-0.5 bg-primary transition-all duration-150"
        style={{ width: `${progress}%` }}
      />
      
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-2 text-muted-foreground hover:text-foreground">
              <ArrowLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Назад</span>
            </Button>
          </Link>
          
          <div className="hidden md:block h-5 w-px bg-border" />
          
          <h1 className="text-sm font-medium truncate max-w-[200px] sm:max-w-[300px] md:max-w-[500px]">
            {title}
          </h1>
        </div>

        <div className="flex items-center gap-1">
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8" 
            onClick={cycleTheme}
          >
            <ThemeIcon className="h-4 w-4" />
          </Button>
          
          <LecturePublicSettings 
            settings={settings} 
            onUpdate={onUpdateSettings} 
          />
        </div>
      </div>
    </header>
  );
}
