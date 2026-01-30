import { Bug, Lightbulb, Upload, X, AlertCircle, Info } from 'lucide-react';
import { useDropzone, type FileRejection } from 'react-dropzone';
import Image from 'next/image';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Textarea } from '@/components/ui/textarea';
import type { FeedbackFormValues } from './schema';
import { FEEDBACK_ACCEPT, FEEDBACK_FILE_LIMIT, FEEDBACK_MAX_SIZE, type PendingFile } from './types';
import type { UseFormReturn } from 'react-hook-form';

type FormContentProps = {
  form: UseFormReturn<FeedbackFormValues>;
  files: PendingFile[];
  hasLimit: boolean;
  addFiles: (acceptedFiles: File[], rejectedFiles: FileRejection[]) => void;
  removeFile: (index: number) => void;
};

export function FormContent({ form, files, hasLimit, addFiles, removeFile }: FormContentProps) {
  const selectedType = form.watch('type');
  const { errors } = form.formState;

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop: addFiles,
    accept: FEEDBACK_ACCEPT,
    maxSize: FEEDBACK_MAX_SIZE,
    maxFiles: Math.max(0, FEEDBACK_FILE_LIMIT - files.length),
    disabled: hasLimit,
  });

  return (
    <>
      {/* Type Selection */}
      <div className="space-y-2">
        <Label>Тип обращения</Label>
        <RadioGroup
          value={selectedType}
          onValueChange={(value) => form.setValue('type', value as 'bug' | 'suggestion', { shouldValidate: true })}
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

      {/* Title Field */}
      <div className="space-y-2">
        <Label htmlFor="title">
          Заголовок <span className="text-destructive">*</span>
        </Label>
        <Input
          id="title"
          placeholder={selectedType === 'bug' ? 'Кратко опишите проблему' : 'Суть предложения'}
          {...form.register('title')}
          className={errors.title ? 'border-destructive' : ''}
        />
        {errors.title && (
          <p className="text-sm text-destructive flex items-center gap-1">
            <AlertCircle className="h-4 w-4" />
            {errors.title.message}
          </p>
        )}
        <p className="text-xs text-muted-foreground flex items-center gap-1">
          <Info className="h-3 w-3" />
          Минимум 5, максимум 200 символов
        </p>
      </div>

      {/* Description Field */}
      <div className="space-y-2">
        <Label htmlFor="description">
          Подробное описание <span className="text-destructive">*</span>
        </Label>
        <Textarea
          id="description"
          rows={14}
          className={`min-h-[280px] resize-y font-mono text-sm ${errors.description ? 'border-destructive' : ''}`}
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
        {errors.description && (
          <p className="text-sm text-destructive flex items-center gap-1">
            <AlertCircle className="h-4 w-4" />
            {errors.description.message}
          </p>
        )}
        <p className="text-xs text-muted-foreground flex items-center gap-1">
          <Info className="h-3 w-3" />
          Минимум 20, максимум 10000 символов
        </p>
      </div>

      {/* Attachments Dropzone */}
      <div className="space-y-2">
        <Label>
          Скриншоты (необязательно)
          <span className="text-muted-foreground ml-2">
            {files.length}/{FEEDBACK_FILE_LIMIT}
          </span>
        </Label>
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all
            ${isDragActive && !isDragReject ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
            ${isDragReject ? 'border-destructive bg-destructive/5' : ''}
            ${hasLimit ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />
          <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            {isDragActive
              ? (isDragReject ? 'Файл не поддерживается' : 'Отпустите файлы здесь')
              : hasLimit
                ? 'Достигнут лимит файлов'
                : 'Перетащите скриншоты или кликните для выбора'}
          </p>
          <p className="text-xs text-muted-foreground mt-2">
            Поддерживаются: PNG, JPG, GIF, WebP до 5MB
          </p>
        </div>

        {/* File Previews */}
        {files.length > 0 && (
          <div className="flex flex-wrap gap-3 mt-3">
            {files.map((file, index) => (
              <div key={file.preview} className="relative group">
                <div className="relative">
                  <Image
                    src={file.preview}
                    alt={file.file.name}
                    width={100}
                    height={100}
                    className="h-24 w-24 object-cover rounded-lg border-2 border-border"
                    unoptimized
                  />
                  {/* File size badge */}
                  <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs px-1 py-0.5 rounded-b-lg">
                    {(file.file.size / 1024).toFixed(1)} KB
                  </div>
                </div>
                {/* Remove button */}
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="absolute -top-2 -right-2 bg-destructive text-destructive-foreground rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity shadow-md hover:scale-110"
                  aria-label="Удалить файл"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
