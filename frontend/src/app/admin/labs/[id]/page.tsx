'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { LabsAPI, Lab } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { LectureViewer } from '@/components/lectures/LectureViewer';
import { SerializedEditorState } from 'lexical';
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
import { 
  ArrowLeft, 
  Pencil, 
  Trash2, 
  Globe, 
  GlobeLock,
  Copy,
  Check,
  Loader2,
  Target,
  BookOpen,
  Code,
  HelpCircle,
  Calendar,
  Hash
} from 'lucide-react';
import Link from 'next/link';

export default function LabViewPage() {
  const params = useParams();
  const router = useRouter();
  const labId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [lab, setLab] = useState<Lab | null>(null);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeSection, setActiveSection] = useState<'theory' | 'practice'>('theory');

  useEffect(() => {
    loadLab();
  }, [labId]);

  const loadLab = async () => {
    try {
      const data = await LabsAPI.adminGet(labId);
      setLab(data);
    } catch {
      toast.error('Ошибка загрузки лабораторной');
      router.push('/admin/labs');
    } finally {
      setLoading(false);
    }
  };

  const handlePublishToggle = async () => {
    if (!lab) return;
    setIsPublishing(true);
    try {
      if (lab.is_published) {
        await LabsAPI.adminUnpublish(labId);
        setLab({ ...lab, is_published: false, public_code: null });
        toast.success('Лабораторная снята с публикации');
      } else {
        const result = await LabsAPI.adminPublish(labId);
        setLab({ ...lab, is_published: true, public_code: result.public_code });
        toast.success('Лабораторная опубликована');
      }
    } catch {
      toast.error('Ошибка публикации');
    } finally {
      setIsPublishing(false);
    }
  };

  const handleDelete = async () => {
    if (!lab) return;
    setIsDeleting(true);
    try {
      await LabsAPI.adminDelete(labId);
      toast.success('Лабораторная удалена');
      router.push('/admin/labs');
    } catch {
      toast.error('Ошибка удаления');
      setIsDeleting(false);
    }
  };

  const copyPublicLink = async () => {
    if (!lab?.public_code) return;
    const url = `${window.location.origin}/labs/view/${lab.public_code}`;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    toast.success('Ссылка скопирована');
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-[600px] rounded-xl" />
      </div>
    );
  }

  if (!lab) return null;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/admin/labs">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Hash className="h-6 w-6 text-muted-foreground" />
              {lab.number}. {lab.title}
              {lab.is_published && (
                <Badge variant="secondary" className="gap-1 ml-2">
                  <Globe className="h-3 w-3" />
                  Опубликовано
                </Badge>
              )}
            </h1>
            <p className="text-muted-foreground">{lab.topic}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Copy link button */}
          {lab.is_published && lab.public_code && (
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
          )}

          {/* Publish button */}
          <Button
            variant={lab.is_published ? 'outline' : 'default'}
            size="sm"
            onClick={handlePublishToggle}
            disabled={isPublishing}
            className="gap-1.5"
          >
            {isPublishing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : lab.is_published ? (
              <GlobeLock className="h-4 w-4" />
            ) : (
              <Globe className="h-4 w-4" />
            )}
            {lab.is_published ? 'Снять с публикации' : 'Опубликовать'}
          </Button>

          {/* Edit button */}
          <Link href={`/admin/labs/${labId}/edit`}>
            <Button variant="outline" size="sm" className="gap-1.5">
              <Pencil className="h-4 w-4" />
              Редактировать
            </Button>
          </Link>

          {/* Delete button */}
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="icon" className="text-destructive">
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Удалить лабораторную?</AlertDialogTitle>
                <AlertDialogDescription>
                  Это действие нельзя отменить. Лабораторная &quot;{lab.title}&quot; будет удалена навсегда.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Отмена</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  {isDeleting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                  Удалить
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      {/* Info badges */}
      <div className="flex flex-wrap gap-2">
        <Badge variant="secondary" className="gap-1">
          <Target className="h-3 w-3" />
          Макс. оценка: {lab.max_grade}
        </Badge>
        {lab.deadline && (
          <Badge variant="outline" className="gap-1">
            <Calendar className="h-3 w-3" />
            Дедлайн: {new Date(lab.deadline).toLocaleDateString('ru-RU')}
          </Badge>
        )}
        {lab.is_sequential && (
          <Badge variant="outline">Последовательная сдача</Badge>
        )}
        <Badge variant="outline">{lab.variants?.length || 0} вариантов</Badge>
        <Badge variant="outline">{lab.questions?.length || 0} вопросов</Badge>
      </div>

      {/* Goal */}
      {lab.goal && (
        <Card>
          <CardHeader className="py-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4" />
              Цель работы
            </CardTitle>
          </CardHeader>
          <CardContent className="py-3">
            <p className="text-sm">{lab.goal}</p>
          </CardContent>
        </Card>
      )}

      {/* Formatting guide */}
      {lab.formatting_guide && (
        <Card>
          <CardHeader className="py-3">
            <CardTitle className="text-base">Что записать в тетрадь</CardTitle>
          </CardHeader>
          <CardContent className="py-3">
            <pre className="text-sm whitespace-pre-wrap font-sans">{lab.formatting_guide}</pre>
          </CardContent>
        </Card>
      )}

      {/* Content tabs */}
      <div className="flex gap-2 border-b">
        <Button
          variant={activeSection === 'theory' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveSection('theory')}
          className="gap-1.5"
        >
          <BookOpen className="h-4 w-4" />
          Теория
        </Button>
        <Button
          variant={activeSection === 'practice' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveSection('practice')}
          className="gap-1.5"
        >
          <Code className="h-4 w-4" />
          Практика
        </Button>
      </div>

      {/* Theory content */}
      {activeSection === 'theory' && lab.theory_content && (
        <Card>
          <CardContent className="py-6">
            <LectureViewer
              content={lab.theory_content as SerializedEditorState}
              title=""
            />
          </CardContent>
        </Card>
      )}

      {/* Practice content */}
      {activeSection === 'practice' && (
        <div className="space-y-4">
          {lab.practice_content && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base">Общее задание</CardTitle>
              </CardHeader>
              <CardContent className="py-3">
                <LectureViewer
                  content={lab.practice_content as SerializedEditorState}
                  title=""
                />
              </CardContent>
            </Card>
          )}

          {/* Variants */}
          {lab.variants && lab.variants.length > 0 && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base">Варианты ({lab.variants.length})</CardTitle>
              </CardHeader>
              <CardContent className="py-3 space-y-3">
                {lab.variants.map((v: { number: number; description: string; test_data?: string }, i: number) => (
                  <div key={i} className="flex gap-3 p-3 rounded-lg border bg-muted/30">
                    <Badge variant="secondary" className="h-6 w-6 flex items-center justify-center shrink-0">
                      {v.number}
                    </Badge>
                    <div className="flex-1">
                      <p className="font-medium">{v.description || 'Без описания'}</p>
                      {v.test_data && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Тестовые данные: {v.test_data}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Questions */}
      {lab.questions && lab.questions.length > 0 && (
        <Card>
          <CardHeader className="py-3">
            <CardTitle className="text-base flex items-center gap-2">
              <HelpCircle className="h-4 w-4" />
              Контрольные вопросы ({lab.questions.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="py-3">
            <ol className="space-y-2 list-decimal list-inside">
              {lab.questions.map((q: string, i: number) => (
                <li key={i} className="text-sm">{q}</li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
