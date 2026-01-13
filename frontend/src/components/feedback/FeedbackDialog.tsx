'use client';

import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Bug, Lightbulb, MessageSquarePlus, X, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { useDropzone } from 'react-dropzone';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import api from '@/lib/api';

const MAX_FILES = 5;
const MAX_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];

const feedbackSchema = z.object({
  type: z.enum(['bug', 'suggestion']),
  title: z.string().min(5, 'Минимум 5 символов').max(200, 'Максимум 200 символов'),
  description: z.string().min(20, 'Минимум 20 символов').max(10000),
});

type FeedbackForm = z.infer<typeof feedbackSchema>;

interface PendingFile {
  file: File;
  preview: string;
}

interface FeedbackDialogProps {
  trigger?: React.ReactNode;
}

export function FeedbackDialog({ trigger }: FeedbackDialogProps) {
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [files, setFiles] = useState<PendingFile[]>([]);

  const form = useForm<FeedbackForm>({
    resolver: zodResolver(feedbackSchema),
    defaultValues: { type: 'bug', title: '', description: '' },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const remaining = MAX_FILES - files.length;
    const toAdd = acceptedFiles.slice(0, remaining);
    
    const newFiles = toAdd.map(file => ({
      file,
      preview: URL.createObjectURL(file),
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
  }, [files.length]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'] },
    maxSize: MAX_SIZE,
    maxFiles: MAX_FILES - files.length,
    disabled: files.length >= MAX_FILES,
  });

  const removeFile = (index: number) => {
    setFiles(prev => {
      URL.revokeObjectURL(prev[index].preview);
      return prev.filter((_, i) => i !== index);
    });
  };

  const uploadAttachment = async (feedbackId: string, file: File): Promise<boolean> => {
    try {
      // Get presigned URL
      const params = new URLSearchParams({
        filename: file.name,
        content_type: file.type,
        size: file.size.toString(),
      });
      const { data } = await api.post(`/feedback/${feedbackId}/attachments?${params}`);
      
      // Upload to MinIO
      await fetch(data.upload_url, {
        method: 'PUT',
        body: file,
        headers: { 'Content-Type': file.type },
      });
      return true;
    } catch (e) {
      console.error('Upload failed:', e);
      return false;
    }
  };

  const onSubmit = async (data: FeedbackForm) => {
    try {
      setSubmitting(true);
      
      // Create feedback
      const { data: feedback } = await api.post('/feedback', data);
      
      // Upload attachments
      if (files.length > 0) {
        const results = await Promise.all(
          files.map(f => uploadAttachment(feedback.id, f.file))
        );
        const failed = results.filter(r => !r).length;
        if (failed > 0) {
          toast.warning(`${failed} файл(ов) не загружено`);
        }
      }
      
      toast.success('Спасибо за обратную связь!');
      setOpen(false);
      form.reset();
      files.forEach(f => URL.revokeObjectURL(f.preview));
      setFiles([]);
    } catch {
      toast.error('Не удалось отправить');
    } finally {
      setSubmitting(false);
    }
  };

  const selectedType = form.watch('type');

  return (
    <Dialog open={open} onOpenChange={(v) => {
      setOpen(v);
      if (!v) {
        files.forEach(f => URL.revokeObjectURL(f.preview));
        setFiles([]);
        form.reset();
      }
    }}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="ghost" size="icon" title="Обратная связь">
            <MessageSquarePlus className="h-5 w-5" />
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Обратная связь</DialogTitle>
          <DialogDescription>
            Сообщите об ошибке или предложите улучшение
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label>Тип обращения</Label>
            <RadioGroup
              value={selectedType}
              onValueChange={(v) => form.setValue('type', v as 'bug' | 'suggestion')}
              className="flex gap-4"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="bug" id="bug" />
                <Label htmlFor="bug" className="flex items-center gap-1 cursor-pointer">
                  <Bug className="h-4 w-4 text-red-500" />
                  Ошибка
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="suggestion" id="suggestion" />
                <Label htmlFor="suggestion" className="flex items-center gap-1 cursor-pointer">
                  <Lightbulb className="h-4 w-4 text-yellow-500" />
                  Предложение
                </Label>
              </div>
            </RadioGroup>
          </div>

          <div className="space-y-2">
            <Label htmlFor="title">Заголовок</Label>
            <Input
              id="title"
              placeholder={selectedType === 'bug' ? 'Кратко опишите проблему' : 'Суть предложения'}
              {...form.register('title')}
            />
            {form.formState.errors.title && (
              <p className="text-sm text-red-500">{form.formState.errors.title.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Подробное описание</Label>
            <Textarea
              id="description"
              rows={14}
              className="min-h-[280px] resize-y font-mono text-sm"
              placeholder={
                selectedType === 'bug'
                  ? `Опишите проблему:

• Что произошло?
• Какие действия выполняли?
• На какой странице?
• Повторяется ли ошибка?`
                  : `Опишите идею:

• В чём суть?
• Какую проблему решит?
• Как улучшит работу?`
              }
              {...form.register('description')}
            />
            {form.formState.errors.description && (
              <p className="text-sm text-red-500">{form.formState.errors.description.message}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Минимум 20 символов, максимум 10000
            </p>
          </div>

          {/* File upload */}
          <div className="space-y-2">
            <Label>Скриншоты (до {MAX_FILES} файлов)</Label>
            <div
              {...getRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors
                ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
                ${files.length >= MAX_FILES ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <input {...getInputProps()} />
              <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                {isDragActive
                  ? 'Отпустите файлы...'
                  : files.length >= MAX_FILES
                    ? 'Достигнут лимит файлов'
                    : 'Перетащите скриншоты или кликните для выбора'}
              </p>
              <p className="text-xs text-muted-foreground mt-1">PNG, JPG, GIF, WebP до 5MB</p>
            </div>

            {/* Preview */}
            {files.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {files.map((f, i) => (
                  <div key={i} className="relative group">
                    <img
                      src={f.preview}
                      alt={f.file.name}
                      className="h-20 w-20 object-cover rounded border"
                    />
                    <button
                      type="button"
                      onClick={() => removeFile(i)}
                      className="absolute -top-2 -right-2 bg-destructive text-destructive-foreground rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Отправка...' : 'Отправить'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
