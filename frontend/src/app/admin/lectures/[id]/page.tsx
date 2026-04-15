'use client';

import dynamic from 'next/dynamic';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import type { SerializedEditorState } from 'lexical';
import { Button } from '@/components/ui/button';
import { TooltipProvider } from '@/components/ui/tooltip';
import { toast } from 'sonner';
import { Loader2, EyeOff } from 'lucide-react';
import { LectureEditor } from '@/components/lectures/LectureEditor';
import { LectureEditorHeader } from '@/components/lectures/admin/LectureEditorHeader';
import {
  loadAdminLectureDetail,
  peekAdminLectureDetail,
  primeAdminLectureDetail,
} from '@/lib/admin-lectures-cache';
import { LecturesAPI, type LectureResponse } from '@/lib/lectures-api';
import { cn } from '@/lib/utils';

const LectureViewer = dynamic(
  () => import('@/components/lectures/LectureViewer').then((module) => module.LectureViewer),
  {
    ssr: false,
    loading: () => <div className="min-h-[280px] animate-pulse rounded-lg bg-muted/50" />,
  },
);

const emptyEditorState = {
  root: {
    children: [{ children: [], direction: null, format: '', indent: 0, type: 'paragraph', version: 1 }],
    direction: null,
    format: '',
    indent: 0,
    type: 'root',
    version: 1,
  },
};

type PreviewMode = 'off' | 'split' | 'full';

export default function LectureEditorPage() {
  const params = useParams();
  const router = useRouter();
  const lectureId = params.id as string;
  const isNew = lectureId === 'new';

  const [lecture, setLecture] = useState<LectureResponse | null>(null);
  const [title, setTitle] = useState('');
  const [isLoading, setIsLoading] = useState(!isNew);
  const [previewMode, setPreviewMode] = useState<PreviewMode>('off');
  const [previewContent, setPreviewContent] = useState<SerializedEditorState | null>(null);
  const [debouncedPreviewContent, setDebouncedPreviewContent] = useState<SerializedEditorState | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!previewContent) {
      return;
    }

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      setDebouncedPreviewContent(previewContent);
    }, 300);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [previewContent]);

  useEffect(() => {
    if (isNew) {
      setTitle('Новая лекция');
      setPreviewContent(emptyEditorState as unknown as SerializedEditorState);
      setDebouncedPreviewContent(emptyEditorState as unknown as SerializedEditorState);
      setIsLoading(false);
      return;
    }

    let isMounted = true;
    const cachedLecture = peekAdminLectureDetail(lectureId);

    if (cachedLecture) {
      setLecture(cachedLecture);
      setTitle(cachedLecture.title);
      setPreviewContent(cachedLecture.content as unknown as SerializedEditorState);
      setDebouncedPreviewContent(cachedLecture.content as unknown as SerializedEditorState);
      setIsLoading(false);
      return () => {
        isMounted = false;
      };
    }

    const loadLecture = async () => {
      setIsLoading(true);

      try {
        const data = await loadAdminLectureDetail(lectureId, () => LecturesAPI.get(lectureId));
        if (!isMounted) {
          return;
        }

        setLecture(data);
        setTitle(data.title);
        setPreviewContent(data.content as unknown as SerializedEditorState);
        setDebouncedPreviewContent(data.content as unknown as SerializedEditorState);
      } catch {
        if (!isMounted) {
          return;
        }

        toast.error('Не удалось загрузить лекцию');
        router.push('/admin/lectures');
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void loadLecture();

    return () => {
      isMounted = false;
    };
  }, [lectureId, isNew, router]);

  const handleSave = useCallback(async (content: SerializedEditorState) => {
    setPreviewContent(content);

    try {
      if (isNew) {
        const created = await LecturesAPI.create({ title, content });
        primeAdminLectureDetail(created);
        setLecture(created);
        router.prefetch(`/admin/lectures/${created.id}`);
        router.replace(`/admin/lectures/${created.id}`);
        toast.success('Лекция создана');
        return;
      }

      const updated = await LecturesAPI.update(lectureId, { title, content });
      primeAdminLectureDetail(updated);
      setLecture(updated);
    } catch (error) {
      toast.error('Ошибка сохранения');
      throw error;
    }
  }, [isNew, lectureId, router, title]);

  const handleContentChange = useCallback((content: SerializedEditorState) => {
    setPreviewContent(content);
  }, []);

  const togglePreview = useCallback(() => {
    setPreviewMode((currentMode) => {
      if (currentMode === 'off') return 'split';
      if (currentMode === 'split') return 'full';
      return 'off';
    });
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="space-y-4">
        <LectureEditorHeader
          lecture={lecture}
          title={title}
          onTitleChange={setTitle}
          isNew={isNew}
          previewMode={previewMode}
          onTogglePreview={togglePreview}
          onLectureUpdate={(nextLecture) => {
            primeAdminLectureDetail(nextLecture);
            setLecture(nextLecture);
          }}
          content={previewContent}
        />

        <div
          className={cn(
            'grid gap-4',
            previewMode === 'split' && 'grid-cols-2',
            previewMode === 'full' && 'grid-cols-1',
          )}
        >
          {previewMode !== 'full' && (
            <LectureEditor
              initialContent={(lecture?.content || emptyEditorState) as unknown as SerializedEditorState}
              onSave={handleSave}
              onChange={handleContentChange}
              autoSaveInterval={30000}
            />
          )}

          {previewMode !== 'off' && debouncedPreviewContent && (
            <div
              className={cn(
                'rounded-lg border bg-background shadow overflow-auto',
                previewMode === 'split' ? 'max-h-[calc(100vh-200px)]' : 'min-h-[400px]',
              )}
            >
              <div className="sticky top-0 z-10 flex items-center justify-between px-4 py-2 border-b bg-muted/40">
                <span className="text-sm font-medium text-muted-foreground">Предпросмотр</span>
                {previewMode === 'full' && (
                  <Button variant="ghost" size="sm" onClick={() => setPreviewMode('off')} className="gap-1.5">
                    <EyeOff className="h-4 w-4" />
                    Закрыть
                  </Button>
                )}
              </div>
              <div className="p-6">
                <LectureViewer content={debouncedPreviewContent} title={title} />
              </div>
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}
