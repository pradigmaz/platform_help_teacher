'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { SerializedEditorState } from 'lexical';
import { LectureEditor } from '@/components/lectures/LectureEditor';
import { LectureViewer } from '@/components/lectures/LectureViewer';
import { LecturesAPI, type LectureResponse } from '@/lib/lectures-api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipTrigger,
  TooltipProvider 
} from '@/components/ui/tooltip';
import { toast } from 'sonner';
import { 
  ArrowLeft, 
  Globe, 
  GlobeLock, 
  Copy, 
  Check,
  Loader2,
  FileDown,
  Trash2,
  Eye,
  EyeOff,
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { cn } from '@/lib/utils';

// Initial empty editor state
const emptyEditorState = {
  root: {
    children: [
      {
        children: [],
        direction: null,
        format: '',
        indent: 0,
        type: 'paragraph',
        version: 1,
      },
    ],
    direction: null,
    format: '',
    indent: 0,
    type: 'root',
    version: 1,
  },
};

export default function LectureEditorPage() {
  const params = useParams();
  const router = useRouter();
  const lectureId = params.id as string;
  const isNew = lectureId === 'new';

  const [lecture, setLecture] = useState<LectureResponse | null>(null);
  const [title, setTitle] = useState('');
  const [isLoading, setIsLoading] = useState(!isNew);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [copied, setCopied] = useState(false);
  
  // Preview mode state
  const [previewMode, setPreviewMode] = useState<'off' | 'split' | 'full'>('off');
  const [previewContent, setPreviewContent] = useState<SerializedEditorState | null>(null);
  const [debouncedPreviewContent, setDebouncedPreviewContent] = useState<SerializedEditorState | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Debounce preview content updates
  useEffect(() => {
    if (previewContent) {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      debounceTimerRef.current = setTimeout(() => {
        setDebouncedPreviewContent(previewContent);
      }, 300);
    }
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [previewContent]);

  // Load lecture data
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
        console.error('Failed to load lecture:', error);
        toast.error('Не удалось загрузить лекцию');
        router.push('/admin/lectures');
      } finally {
        setIsLoading(false);
      }
    };

    loadLecture();
  }, [lectureId, isNew, router]);

  // Save handler
  const handleSave = useCallback(async (content: SerializedEditorState) => {
    // Update preview content
    setPreviewContent(content);
    
    try {
      if (isNew) {
        // Create new lecture
        const created = await LecturesAPI.create({ 
          title, 
          content 
        });
        setLecture(created);
        // Redirect to edit page with new ID
        router.replace(`/admin/lectures/${created.id}`);
        toast.success('Лекция создана');
      } else {
        // Update existing
        const updated = await LecturesAPI.update(lectureId, { 
          title, 
          content 
        });
        setLecture(updated);
      }
    } catch (error) {
      console.error('Save error:', error);
      toast.error('Ошибка сохранения');
      throw error;
    }
  }, [isNew, lectureId, title, router]);

  // Handle content change for live preview
  const handleContentChange = useCallback((content: SerializedEditorState) => {
    setPreviewContent(content);
  }, []);

  // Toggle preview mode
  const togglePreview = useCallback(() => {
    setPreviewMode(prev => {
      if (prev === 'off') return 'split';
      if (prev === 'split') return 'full';
      return 'off';
    });
  }, []);

  // Publish/unpublish handler
  const handlePublishToggle = async () => {
    if (!lecture) return;
    
    setIsPublishing(true);
    try {
      if (lecture.is_published) {
        await LecturesAPI.unpublish(lecture.id);
        setLecture({ ...lecture, is_published: false, public_code: null });
        toast.success('Лекция снята с публикации');
      } else {
        const result = await LecturesAPI.publish(lecture.id);
        setLecture({ ...lecture, is_published: true, public_code: result.public_code });
        toast.success('Лекция опубликована');
      }
    } catch (error) {
      console.error('Publish error:', error);
      toast.error('Ошибка публикации');
    } finally {
      setIsPublishing(false);
    }
  };

  // Copy public link
  const copyPublicLink = async () => {
    if (!lecture?.public_code) return;
    
    const url = `${window.location.origin}/lectures/view/${lecture.public_code}`;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    toast.success('Ссылка скопирована');
    setTimeout(() => setCopied(false), 2000);
  };

  // Delete handler
  const handleDelete = async () => {
    if (!lecture) return;
    
    setIsDeleting(true);
    try {
      await LecturesAPI.delete(lecture.id);
      toast.success('Лекция удалена');
      router.push('/admin/lectures');
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Ошибка удаления');
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const publicUrl = lecture?.public_code 
    ? `${typeof window !== 'undefined' ? window.location.origin : ''}/lectures/view/${lecture.public_code}`
    : null;

  return (
    <TooltipProvider>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push('/admin/lectures')}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Название лекции"
              className="text-lg font-semibold w-[300px] md:w-[400px]"
            />

            {lecture?.is_published && (
              <Badge variant="secondary" className="gap-1">
                <Globe className="h-3 w-3" />
                Опубликовано
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Public link */}
            {lecture?.is_published && publicUrl && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={copyPublicLink}
                    className="gap-1.5"
                  >
                    {copied ? (
                      <Check className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                    Копировать ссылку
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">{publicUrl}</p>
                </TooltipContent>
              </Tooltip>
            )}

            {/* Publish button */}
            {!isNew && lecture && (
              <Button
                variant={lecture.is_published ? 'outline' : 'default'}
                size="sm"
                onClick={handlePublishToggle}
                disabled={isPublishing}
                className="gap-1.5"
              >
                {isPublishing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : lecture.is_published ? (
                  <GlobeLock className="h-4 w-4" />
                ) : (
                  <Globe className="h-4 w-4" />
                )}
                {lecture.is_published ? 'Снять с публикации' : 'Опубликовать'}
              </Button>
            )}

            {/* PDF export (placeholder) */}
            {!isNew && lecture && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="icon" disabled>
                    <FileDown className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Экспорт в PDF (скоро)</p>
                </TooltipContent>
              </Tooltip>
            )}

            {/* Preview toggle */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant={previewMode !== 'off' ? 'default' : 'outline'} 
                  size="sm"
                  onClick={togglePreview}
                  className="gap-1.5"
                >
                  {previewMode === 'off' ? (
                    <Eye className="h-4 w-4" />
                  ) : previewMode === 'split' ? (
                    <PanelLeft className="h-4 w-4" />
                  ) : (
                    <EyeOff className="h-4 w-4" />
                  )}
                  {previewMode === 'off' ? 'Предпросмотр' : previewMode === 'split' ? 'Разделить' : 'Закрыть'}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>
                  {previewMode === 'off' 
                    ? 'Показать предпросмотр (разделённый экран)' 
                    : previewMode === 'split'
                    ? 'Показать только предпросмотр'
                    : 'Вернуться к редактору'
                  }
                </p>
              </TooltipContent>
            </Tooltip>

            {/* Delete button */}
            {!isNew && lecture && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" size="icon" className="text-destructive">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Удалить лекцию?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Это действие нельзя отменить. Лекция &quot;{lecture.title}&quot; будет удалена навсегда.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Отмена</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleDelete}
                      disabled={isDeleting}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      {isDeleting ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : null}
                      Удалить
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>

        {/* Editor and Preview */}
        <div className={cn(
          "grid gap-4",
          previewMode === 'split' && "grid-cols-2",
          previewMode === 'full' && "grid-cols-1"
        )}>
          {/* Editor */}
          {previewMode !== 'full' && (
            <LectureEditor
              initialContent={(lecture?.content || emptyEditorState) as SerializedEditorState}
              onSave={handleSave}
              onChange={handleContentChange}
              autoSaveInterval={30000}
            />
          )}
          
          {/* Preview */}
          {previewMode !== 'off' && debouncedPreviewContent && (
            <div className={cn(
              "rounded-lg border bg-background shadow overflow-auto",
              previewMode === 'split' ? "max-h-[calc(100vh-200px)]" : "min-h-[400px]"
            )}>
              <div className="sticky top-0 z-10 flex items-center justify-between px-4 py-2 border-b bg-muted/40">
                <span className="text-sm font-medium text-muted-foreground">Предпросмотр</span>
                {previewMode === 'full' && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setPreviewMode('off')}
                    className="gap-1.5"
                  >
                    <EyeOff className="h-4 w-4" />
                    Закрыть
                  </Button>
                )}
              </div>
              <div className="p-6">
                <LectureViewer
                  content={debouncedPreviewContent}
                  title={title}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}
