'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  MoreVertical, 
  Pencil, 
  Trash2, 
  Link2, 
  Link2Off, 
  Download,
  FileText,
  Copy,
  ExternalLink,
  GraduationCap
} from 'lucide-react';
import type { LectureListResponse } from '@/lib/lectures-api';

interface LectureCardProps {
  lecture: LectureListResponse;
  onDelete: (id: string, title: string) => void;
  onPublish: (id: string) => void;
  onUnpublish: (id: string) => void;
  onWarmup?: () => void;
  onCopyLink: (code: string) => void;
  onExportPdf: (id: string, title: string) => void;
  onExportMarkdown: (id: string, title: string) => void;
}

export function LectureCard({
  lecture,
  onDelete,
  onPublish,
  onUnpublish,
  onWarmup,
  onCopyLink,
  onExportPdf,
  onExportMarkdown,
}: LectureCardProps) {
  const router = useRouter();

  return (
    <Card
      className="group h-full cursor-pointer border-border/60 bg-card/95 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/25 hover:shadow-lg hover:bg-accent/10"
      onMouseEnter={onWarmup}
      onFocus={onWarmup}
    >
      <div className="p-5 h-full flex flex-col">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h3 
              className="cursor-pointer truncate text-lg font-semibold transition-colors group-hover:text-primary"
              onClick={() => router.push(`/admin/lectures/${lecture.id}`)}
            >
              {lecture.title}
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              {new Date(lecture.updated_at).toLocaleDateString('ru-RU', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
              })}
            </p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => router.push(`/admin/lectures/${lecture.id}`)}>
                <Pencil className="mr-2 h-4 w-4" /> Редактировать
              </DropdownMenuItem>
              {lecture.is_published ? (
                <>
                  <DropdownMenuItem onClick={() => onCopyLink(lecture.public_code!)}>
                    <Copy className="mr-2 h-4 w-4" /> Копировать ссылку
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => window.open(`/lectures/view/${lecture.public_code}`, '_blank')}>
                    <ExternalLink className="mr-2 h-4 w-4" /> Открыть
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onUnpublish(lecture.id)}>
                    <Link2Off className="mr-2 h-4 w-4" /> Снять публикацию
                  </DropdownMenuItem>
                </>
              ) : (
                <DropdownMenuItem onClick={() => onPublish(lecture.id)}>
                  <Link2 className="mr-2 h-4 w-4" /> Опубликовать
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={() => onExportPdf(lecture.id, lecture.title)}>
                <Download className="mr-2 h-4 w-4" /> Экспорт PDF
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onExportMarkdown(lecture.id, lecture.title)}>
                <FileText className="mr-2 h-4 w-4" /> Скачать Markdown
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => onDelete(lecture.id, lecture.title)}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" /> Удалить
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="mt-auto pt-3 flex items-center gap-2 flex-wrap">
          {lecture.subject && (
            <Badge variant="outline" className="text-xs">
              <GraduationCap className="mr-1 h-3 w-3" />
              {lecture.subject.code || lecture.subject.name}
            </Badge>
          )}
          {lecture.is_published ? (
            <Badge variant="secondary" className="bg-green-500/10 text-green-600 border-green-500/30">
              <Link2 className="mr-1 h-3 w-3" /> Опубликовано
            </Badge>
          ) : (
            <Badge variant="secondary" className="bg-muted">
              Черновик
            </Badge>
          )}
        </div>
      </div>
    </Card>
  );
}
