'use client';

import { useState } from 'react';
import { Settings, Sun, Moon, BookOpen, Type, X, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { ReaderSettings, Theme, FontFamily } from './types';

interface Props {
  settings: ReaderSettings;
  onUpdate: (settings: Partial<ReaderSettings>) => void;
}

export function LecturePublicSettings({ settings, onUpdate }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  const themes: { id: Theme; label: string; icon: typeof Sun }[] = [
    { id: 'light', label: 'Светлая', icon: Sun },
    { id: 'sepia', label: 'Сепия', icon: BookOpen },
    { id: 'dark', label: 'Тёмная', icon: Moon },
  ];

  const fonts: { id: FontFamily; label: string }[] = [
    { id: 'sans', label: 'Sans' },
    { id: 'serif', label: 'Serif' },
    { id: 'mono', label: 'Mono' },
  ];

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Settings className="h-4 w-4" />
      </Button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)} 
          />
          <div className="absolute right-0 top-full mt-2 w-72 p-4 rounded-xl shadow-xl bg-popover border border-border z-50 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-border">
              <h3 className="font-semibold">
                Настройки чтения
              </h3>
              <button 
                onClick={() => setIsOpen(false)} 
                className="text-muted-foreground hover:text-foreground"
              >
                <X size={18} />
              </button>
            </div>

            {/* Theme */}
            <div className="mb-6">
              <label className="text-xs font-bold text-muted-foreground uppercase mb-3 block">
                Тема
              </label>
              <div className="grid grid-cols-3 gap-2">
                {themes.map((theme) => (
                  <button
                    key={theme.id}
                    onClick={() => onUpdate({ theme: theme.id })}
                    className={cn(
                      "flex flex-col items-center justify-center p-2 rounded-lg border transition-all",
                      settings.theme === theme.id
                        ? "bg-primary/10 border-primary text-primary"
                        : "border-border text-muted-foreground hover:bg-accent"
                    )}
                  >
                    <theme.icon size={18} className="mb-1" />
                    <span className="text-xs font-medium">{theme.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Font Family */}
            <div className="mb-6">
              <label className="text-xs font-bold text-muted-foreground uppercase mb-3 block">
                Шрифт
              </label>
              <div className="space-y-1">
                {fonts.map((font) => (
                  <button
                    key={font.id}
                    onClick={() => onUpdate({ fontFamily: font.id })}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors",
                      font.id === 'sans' && "font-sans",
                      font.id === 'serif' && "font-serif",
                      font.id === 'mono' && "font-mono",
                      settings.fontFamily === font.id
                        ? "bg-primary/10 text-primary"
                        : "hover:bg-accent text-foreground"
                    )}
                  >
                    <span>{font.label}</span>
                    {settings.fontFamily === font.id && <Check size={14} />}
                  </button>
                ))}
              </div>
            </div>

            {/* Font Size */}
            <div>
              <label className="text-xs font-bold text-muted-foreground uppercase mb-3 flex justify-between">
                <span>Размер текста</span>
                <span>{settings.fontSize}px</span>
              </label>
              <div className="flex items-center gap-3">
                <Type size={14} className="text-muted-foreground" />
                <input
                  type="range"
                  min="14"
                  max="24"
                  step="1"
                  value={settings.fontSize}
                  onChange={(e) => onUpdate({ fontSize: parseInt(e.target.value) })}
                  className="flex-1 accent-primary h-1 bg-muted rounded-lg appearance-none cursor-pointer"
                />
                <Type size={20} />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
