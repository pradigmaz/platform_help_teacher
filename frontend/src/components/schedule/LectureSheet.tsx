'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Save, GripVertical } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import api from '@/lib/api';
import type { GroupedLecture, LessonStatus } from './types';
import { useLectureData } from './hooks/useLectureData';
import { LectureSheetHeader } from './components/LectureSheetHeader';
import { LessonStatus as LessonStatusComponent } from './components/LessonStatus';
import { GroupAccordionItem } from './components/GroupAccordionItem';

interface LectureSheetProps {
  lecture: GroupedLecture | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (status?: LessonStatus) => void;
}

function getInitialStatus(lecture: GroupedLecture | null): LessonStatus {
  if (!lecture) return 'normal';
  if (lecture.is_cancelled) return 'cancelled';
  if (lecture.ended_early) return 'early';
  return 'normal';
}

export function LectureSheet({ lecture, isOpen, onClose, onSave }: LectureSheetProps) {
  const [status, setStatus] = useState<LessonStatus>(() => getInitialStatus(lecture));
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [width, setWidth] = useState(450);
  const isResizing = useRef(false);

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

  // Reset status when lecture changes
  useEffect(() => {
    setStatus(getInitialStatus(lecture));
    setHasChanges(false);
  }, [lecture?.date, lecture?.lesson_number, lecture?.subject_id]);

  const {
    groupsData,
    expandedGroups,
    toggleGroup,
    cycleAttendance,
    saveAttendance,
    isLoading,
  } = useLectureData({ lecture, isOpen });

  const handleStatusChange = (newStatus: LessonStatus) => {
    setStatus(newStatus);
    setHasChanges(true);
  };

  const handleAttendanceClick = useCallback((groupId: string, studentId: string) => {
    cycleAttendance(groupId, studentId);
    setHasChanges(true);
  }, [cycleAttendance]);

  const handleSave = async () => {
    if (!lecture) return;
    setIsSaving(true);

    try {
      // Save status for all lessons in the lecture
      const statusPayload = {
        is_cancelled: status === 'cancelled',
        ended_early: status === 'early',
      };
      
      for (const group of lecture.groups) {
        // Update lesson status
        await api.patch(`/admin/lessons/${group.lesson_id}`, statusPayload);
        // Save attendance
        await saveAttendance(group.id, group.lesson_id);
      }
      
      setHasChanges(false);
      onSave?.(status);
      onClose();
    } catch (err) {
      console.error('Ошибка сохранения', err);
    } finally {
      setIsSaving(false);
    }
  };

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!lecture || !mounted) return null;

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

        <LectureSheetHeader lecture={lecture} onClose={onClose} />

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
          {/* Status */}
          <LessonStatusComponent status={status} onChange={handleStatusChange} />

          {/* Groups accordion */}
          <div className="space-y-2">
            {[...lecture.groups]
              .sort((a, b) => {
                const numA = parseInt(a.name.match(/(\d{3})/)?.[1] || '0');
                const numB = parseInt(b.name.match(/(\d{3})/)?.[1] || '0');
                return numA - numB;
              })
              .map((group) => {
                const groupState = groupsData[group.id] || { 
                  students: [], 
                  attendance: {}, 
                  isLoading: false 
                };

                return (
                  <GroupAccordionItem
                    key={group.id}
                    group={group}
                    students={groupState.students}
                    attendance={groupState.attendance}
                    isExpanded={expandedGroups.includes(group.id)}
                    isLoading={groupState.isLoading}
                    onToggle={() => toggleGroup(group.id)}
                    onAttendanceClick={(studentId) => handleAttendanceClick(group.id, studentId)}
                  />
                );
              })}
          </div>
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 p-4 border-t flex gap-3 bg-background">
          <Button variant="outline" onClick={onClose}>Отмена</Button>
          <Button 
            className="flex-1" 
            onClick={handleSave}
            disabled={isSaving || isLoading || !hasChanges}
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
