'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { SerializedEditorState } from 'lexical';
import { LectureEditor } from '@/components/lectures/LectureEditor';
import { LectureViewer } from '@/components/lectures/LectureViewer';
import { LectureEditorHeader } from '@/components/lectures/admin/LectureEditorHeader';
import { LecturesAPI, type LectureResponse } from '@/lib/lectures-api';
import { Button } from '@/components/ui/button';
import { TooltipProvider } from '@/components/ui/tooltip';
import { toast } from 'sonner';
import { Loader2, EyeOff } from 'lucide-react';
import { cn } from '@/lib/utils';

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

  // Debounce preview content
  useEffect(() => {
    if (previewContent) {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = setTimeout(() => setDebouncedPreviewContent(previewContent), 300);
    }
    return () => { if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current); };
  }, [previewContent]);

  // Load lecture
  useEffect(() => {
    if (isNew) {
      setTitle('Новая лекция');
      setPreviewContent(emptyEditorState as SerializedEditorState);
      setDebouncedPreviewContent(emptyEditorState as SerializedEditorState);
      return;
    }

    const loadLecture = async () => {
      try {
        const data = await LecturesAPI.get(lectureId);
        setLecture(data);
        setTitle(data.title);
        setPreviewContent(data.content as SerializedEditorState);
        setDebouncedPreviewContent(data.content as SerializedEditorState);
      } catch (error) {
        toast.error('Не удалось загрузить лекцию');
        router.push('/admin/lectures');
      } finally {
        setIsLoading(false);
      }
    };
    loadLecture();
  }, [lectureId, isNew, router]);

  const handleSave = useCallback(async (content: SerializedEditorState) => {
    setPreviewContent(content);
    try {
      if (isNew) {
        const created = await LecturesAPI.create({ title, content });
        setLecture(created);
        router.replace(`/admin/lectures/${created.id}`);
        toast.success('Лекция создана');
      } else {
        const updated = await LecturesAPI.update(lectureId, { title, content });
        setLecture(updated);
      }
    } catch (error) {
      toast.error('Ошибка сохранения');
      throw error;
    }
  }, [isNew, lectureId, title, router]);

  const handleContentChange = useCallback((content: SerializedEditorState) => {
    setPreviewContent(content);
  }, []);

  const togglePreview = useCallback(() => {
    setPreviewMode(prev => prev === 'off' ? 'split' : prev === 'split' ? 'full' : 'off');
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
          onLectureUpdate={setLecture}
        />

        <div className={cn(
          "grid gap-4",
          previewMode === 'split' && "grid-cols-2",
          previewMode === 'full' && "grid-cols-1"
        )}>
          {previewMode !== 'full' && (
            <LectureEditor
              initialContent={(lecture?.content || emptyEditorState) as SerializedEditorState}
              onSave={handleSave}
              onChange={handleContentChange}
              autoSaveInterval={30000}
            />
          )}
          
          {previewMode !== 'off' && debouncedPreviewContent && (
            <div className={cn(
              "rounded-lg border bg-background shadow overflow-auto",
              previewMode === 'split' ? "max-h-[calc(100vh-200px)]" : "min-h-[400px]"
            )}>
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
