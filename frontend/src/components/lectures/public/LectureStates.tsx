'use client';

import { motion } from 'motion/react';
import { Loader2, AlertCircle, BookOpen, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

/**
 * Loading state for lecture page
 */
export function LectureLoadingState() {
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

/**
 * Not found state for lecture page
 */
export function LectureNotFoundState() {
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

interface LectureErrorStateProps {
  message: string;
}

/**
 * Error state for lecture page
 */
export function LectureErrorState({ message }: LectureErrorStateProps) {
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
          <p className="text-muted-foreground">{message}</p>
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
