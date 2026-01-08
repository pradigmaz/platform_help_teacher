'use client';

import { motion } from 'motion/react';
import { IconCheck } from '@tabler/icons-react';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { cn } from '@/lib/utils';

interface AppearanceTabProps {
  theme: string | undefined;
  setTheme: (theme: string) => void;
}

export function AppearanceTab({ theme, setTheme }: AppearanceTabProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.2 }}
    >
      <CardSpotlight className="p-8">
        <h3 className="text-lg font-semibold text-foreground mb-6">Тема оформления</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ThemeCard
            active={theme === 'light'}
            onClick={() => setTheme('light')}
            title="Светлая"
            description="Классическая светлая тема"
            preview={
              <div className="h-20 rounded-lg bg-white border-2 border-neutral-300 p-2 space-y-1">
                <div className="h-2 bg-neutral-200 rounded w-3/4" />
                <div className="h-2 bg-neutral-300 rounded w-1/2" />
              </div>
            }
          />
          <ThemeCard
            active={theme === 'dark'}
            onClick={() => setTheme('dark')}
            title="Тёмная"
            description="Современная тёмная тема"
            preview={
              <div className="h-20 rounded-lg bg-neutral-900 border-2 border-neutral-700 p-2 space-y-1">
                <div className="h-2 bg-neutral-700 rounded w-3/4" />
                <div className="h-2 bg-neutral-600 rounded w-1/2" />
              </div>
            }
          />
          <ThemeCard
            active={theme === 'system'}
            onClick={() => setTheme('system')}
            title="Системная"
            description="Следует системным настройкам"
            preview={
              <div className="h-20 rounded-lg bg-gradient-to-r from-white via-neutral-500 to-neutral-900 border-2 border-neutral-500 p-2 space-y-1">
                <div className="h-2 bg-neutral-400 rounded w-3/4" />
                <div className="h-2 bg-neutral-500 rounded w-1/2" />
              </div>
            }
          />
        </div>
      </CardSpotlight>
    </motion.div>
  );
}

function ThemeCard({ active, onClick, title, description, preview }: {
  active: boolean;
  onClick: () => void;
  title: string;
  description: string;
  preview: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "p-4 rounded-xl border-2 transition-all text-left",
        active
          ? "border-primary bg-primary/5 shadow-lg shadow-primary/20"
          : "border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-900/50"
      )}
    >
      <div className="mb-3">{preview}</div>
      <h4 className="font-semibold text-foreground mb-1">{title}</h4>
      <p className="text-xs text-muted-foreground">{description}</p>
      {active && (
        <div className="mt-3 flex items-center gap-1 text-xs text-primary">
          <IconCheck className="h-3 w-3" />
          <span>Активна</span>
        </div>
      )}
    </button>
  );
}
