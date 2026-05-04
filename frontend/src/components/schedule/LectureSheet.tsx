'use client';

import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Save, GripVertical } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import type { GroupedLecture, LessonStatus } from './types';
import { isFutureLessonDate } from './hooks/lessonDateGuards';
import { useLectureData } from './hooks/useLectureData';
import { getGroupedLectureKey, type RestoredLectureDraft, type ScheduleDraftContext } from './hooks/sheetDraftTypes';
import { LectureSheetHeader } from './components/LectureSheetHeader';
import { LessonStatus as LessonStatusComponent } from './components/LessonStatus';
import { GroupAccordionItem } from './components/GroupAccordionItem';
import { buildAttendanceUpdates } from './hooks/lessonSheetState';

interface LectureSheetProps {
  lecture: GroupedLecture | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (status?: LessonStatus) => void;
  draftContext: ScheduleDraftContext;
  restoredDraft?: RestoredLectureDraft | null;
}

const DEFAULT_SHEET_WIDTH = 620;

function getInitialStatus(lecture: GroupedLecture | null): LessonStatus {
  if (!lecture) return 'normal';
  if (lecture.is_cancelled) return 'cancelled';
  if (lecture.ended_early) return 'early';
  return 'normal';
}

export function LectureSheet({
  lecture,
  isOpen,
  onClose,
  onSave,
  draftContext,
  restoredDraft = null,
}: LectureSheetProps) {
  const [status, setStatus] = useState<LessonStatus>(() => getInitialStatus(lecture));
  const [topic, setTopic] = useState(() => lecture?.topic ?? '');
  const [isSaving, setIsSaving] = useState(false);
  const [width, setWidth] = useState(DEFAULT_SHEET_WIDTH);
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
    const nextStatus =
      restoredDraft && lecture && restoredDraft.lectureKey === getGroupedLectureKey(lecture)
        ? restoredDraft.status
        : getInitialStatus(lecture);
    const nextTopic =
      restoredDraft && lecture && restoredDraft.lectureKey === getGroupedLectureKey(lecture)
        ? restoredDraft.topic
        : lecture?.topic ?? '';
    setStatus(nextStatus);
    setTopic(nextTopic);
  }, [lecture, restoredDraft]);

  const {
    groupsData,
    expandedGroups,
    toggleGroup,
    setAttendanceStatus,
    saveLectureSheet,
    isLoading,
  } = useLectureData({ lecture, isOpen, draftContext, restoredDraft });

  const hasChanges = useMemo(() => {
    if (!lecture) {
      return false;
    }

    return (
      status !== getInitialStatus(lecture) ||
      (topic || null) !== (lecture.topic || null) ||
      Object.values(groupsData).some(
        (groupState) =>
          buildAttendanceUpdates(groupState.initialAttendance, groupState.attendance).length > 0
      )
    );
  }, [groupsData, lecture, status, topic]);

  const handleStatusChange = (newStatus: LessonStatus) => {
    setStatus(newStatus);
  };

  const handleAttendanceChange = useCallback((groupId: string, studentId: string, nextStatus: import('./types').AttendanceStatus | null) => {
    setAttendanceStatus(groupId, studentId, nextStatus);
  }, [setAttendanceStatus]);

  const handleSave = async () => {
    if (!lecture) return;
    setIsSaving(true);

    try {
      await saveLectureSheet(status, topic);

      onSave?.(status);
      onClose();
    } catch (err) {
      if ((err as Error).message !== 'future_attendance_blocked') {
        console.error('Ошибка сохранения', err);
      }
    } finally {
      setIsSaving(false);
    }
  };

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!lecture || !mounted) return null;
  const attendanceDisabled = isFutureLessonDate(lecture.date);
  const attendanceDisabledReason = 'Посещаемость можно отмечать только в день занятия или позже';

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

        <LectureSheetHeader
          lecture={lecture}
          topic={topic}
          onTopicChange={setTopic}
          onClose={onClose}
        />

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
                  attendanceDisabled={attendanceDisabled}
                  attendanceDisabledReason={attendanceDisabledReason}
                  onToggle={() => toggleGroup(group.id)}
                  onAttendanceChange={(studentId, nextStatus) => handleAttendanceChange(group.id, studentId, nextStatus)}
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
