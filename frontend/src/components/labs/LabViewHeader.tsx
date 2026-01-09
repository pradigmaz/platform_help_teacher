'use client';

import { useState } from 'react';
import Link from 'next/link';
import { toast } from 'sonner';
import { Lab, LabsAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
  Hash,
} from 'lucide-react';

interface LabViewHeaderProps {
  lab: Lab;
  onLabUpdate: (lab: Lab) => void;
  onDelete: () => void;
}

export function LabViewHeader({ lab, onLabUpdate, onDelete }: LabViewHeaderProps) {
  const [isPublishing, setIsPublishing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [copied, setCopied] = useState(false);

  const handlePublishToggle = async () => {
    setIsPublishing(true);
    try {
      if (lab.is_published) {
        await LabsAPI.adminUnpublish(lab.id);
        onLabUpdate({ ...lab, is_published: false, public_code: null });
        toast.success('Лабораторная снята с публикации');
      } else {
        const result = await LabsAPI.adminPublish(lab.id);
        onLabUpdate({ ...lab, is_published: true, public_code: result.public_code });
        toast.success('Лабораторная опубликована');
      }
    } catch {
      toast.error('Ошибка публикации');
    } finally {
      setIsPublishing(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await LabsAPI.adminDelete(lab.id);
      toast.success('Лабораторная удалена');
      onDelete();
    } catch {
      toast.error('Ошибка удаления');
      setIsDeleting(false);
    }
  };

  const copyPublicLink = async () => {
    if (!lab.public_code) return;
    const url = `${window.location.origin}/labs/view/${lab.public_code}`;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    toast.success('Ссылка скопирована');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
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
        {lab.is_published && lab.public_code && (
          <Button variant="outline" size="sm" onClick={copyPublicLink} className="gap-1.5">
            {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            Копировать ссылку
          </Button>
        )}

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

        <Link href={`/admin/labs/${lab.id}/edit`}>
          <Button variant="outline" size="sm" className="gap-1.5">
            <Pencil className="h-4 w-4" />
            Редактировать
          </Button>
        </Link>

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
  );
}
