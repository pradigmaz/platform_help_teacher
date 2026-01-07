'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipTrigger,
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
import { LecturesAPI, type LectureResponse } from '@/lib/lectures-api';

type PreviewMode = 'off' | 'split' | 'full';

interface LectureEditorHeaderProps {
  lecture: LectureResponse | null;
  title: string;
  onTitleChange: (title: string) => void;
  isNew: boolean;
  previewMode: PreviewMode;
  onTogglePreview: () => void;
  onLectureUpdate: (lecture: LectureResponse) => void;
}

export function LectureEditorHeader({
  lecture,
  title,
  onTitleChange,
  isNew,
  previewMode,
  onTogglePreview,
  onLectureUpdate,
}: LectureEditorHeaderProps) {
  const router = useRouter();
  const [isPublishing, setIsPublishing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [copied, setCopied] = useState(false);

  const handlePublishToggle = async () => {
    if (!lecture) return;
    
    setIsPublishing(true);
    try {
      if (lecture.is_published) {
        await LecturesAPI.unpublish(lecture.id);
        onLectureUpdate({ ...lecture, is_published: false, public_code: null });
        toast.success('Лекция снята с публикации');
      } else {
        const result = await LecturesAPI.publish(lecture.id);
        onLectureUpdate({ ...lecture, is_published: true, public_code: result.public_code });
        toast.success('Лекция опубликована');
      }
    } catch (error) {
      toast.error('Ошибка публикации');
    } finally {
      setIsPublishing(false);
    }
  };

  const copyPublicLink = async () => {
    if (!lecture?.public_code) return;
    
    const url = `${window.location.origin}/lectures/view/${lecture.public_code}`;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    toast.success('Ссылка скопирована');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDelete = async () => {
    if (!lecture) return;
    
    setIsDeleting(true);
    try {
      await LecturesAPI.delete(lecture.id);
      toast.success('Лекция удалена');
      router.push('/admin/lectures');
    } catch (error) {
      toast.error('Ошибка удаления');
      setIsDeleting(false);
    }
  };

  const publicUrl = lecture?.public_code 
    ? `${typeof window !== 'undefined' ? window.location.origin : ''}/lectures/view/${lecture.public_code}`
    : null;

  return (
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
          onChange={(e) => onTitleChange(e.target.value)}
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

        <Tooltip>
          <TooltipTrigger asChild>
            <Button 
              variant={previewMode !== 'off' ? 'default' : 'outline'} 
              size="sm"
              onClick={onTogglePreview}
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
  );
}
