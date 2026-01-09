'use client';
'use no memo';

import { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Save, GripVertical } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import type { LessonData } from './types';
import { canHaveGrade } from './constants';
import { useLessonData } from './hooks/useLessonData';
import { SheetHeader, LessonStatus, LessonTopic, StudentsTable } from './components';

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface LessonSheetData extends LessonData {}

interface LessonSheetProps {
  lesson: LessonData | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: () => void;
}

export function LessonSheet({ lesson, isOpen, onClose, onSave }: LessonSheetProps) {
  const [mounted, setMounted] = useState(false);
  const [width, setWidth] = useState(450);
  const isResizing = useRef(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Resize handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isResizing.current = true;
    document.body.style.cursor = 'ew-resize';
    document.body.style.userSelect = 'none';
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      const newWidth = window.innerWidth - e.clientX;
      setWidth(Math.max(350, Math.min(800, newWidth)));
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const {
    students,
    attendance,
    grades,
    topic,
    status,
    isLoading,
    hasChanges,
    setTopic,
    setStatus,
    cycleAttendance,
    setGrade,
    saveAll,
  } = useLessonData({ lesson, isOpen });

  const handleSave = async () => {
    try {
      await saveAll();
      onSave?.();
      onClose();
    } catch {
      // Error already logged in hook
    }
  };

  if (!lesson || !mounted) return null;

  const lessonCanHaveGrade = canHaveGrade(lesson.lesson_type);

  const content = (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          'fixed inset-0 z-[9998] bg-black/60 backdrop-blur-sm transition-opacity duration-300',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={onClose}
      />

      {/* Sheet */}
      <div
        className={cn(
          'fixed top-0 right-0 bottom-0 z-[9999] bg-background border-l shadow-2xl',
          'transform transition-transform duration-300 ease-out flex flex-col h-screen',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
        style={{ width }}
      >
        {/* Resize handle */}
        <div
          onMouseDown={handleMouseDown}
          className="absolute left-0 top-0 bottom-0 w-1 cursor-ew-resize hover:bg-primary/50 transition-colors group flex items-center"
        >
          <div className="absolute left-0 w-4 h-12 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <GripVertical className="h-4 w-4 text-muted-foreground" />
          </div>
        </div>

        <SheetHeader lesson={lesson} onClose={onClose} />

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6 min-h-0">
          <LessonStatus status={status} onChange={setStatus} />
          <LessonTopic lesson={lesson} topic={topic} onChange={setTopic} />
          <StudentsTable
            students={students}
            attendance={attendance}
            grades={grades}
            canHaveGrade={lessonCanHaveGrade}
            isLoading={isLoading}
            onAttendanceClick={cycleAttendance}
            onGradeClick={setGrade}
          />
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 p-4 border-t flex gap-3 bg-background">
          <Button variant="outline" onClick={onClose}>Отмена</Button>
          <Button 
            className="flex-1" 
            onClick={handleSave}
            disabled={isLoading || !hasChanges}
          >
            <Save className="h-4 w-4 mr-2" />
            {hasChanges ? 'Сохранить изменения' : 'Сохранено'}
          </Button>
        </div>
      </div>
    </>
  );

  return createPortal(content, document.body);
}
