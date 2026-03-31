import type { RefObject } from 'react';
import { ClipboardPaste, Plus, Upload, X } from 'lucide-react';
import type { StudentImport } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Dropzone } from '@/components/animate-ui/dropzone';
import { cn } from '@/lib/utils';

interface StudentImportStepProps {
  step: 1 | 2;
  fileInputRef: RefObject<HTMLInputElement | null>;
  students: StudentImport[];
  isUploading: boolean;
  onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  onProcessFile: (file: File) => Promise<void>;
  onOpenPasteModal: () => void;
  onAddEmptyRow: () => void;
  onUpdateStudent: (index: number, field: keyof StudentImport, value: string) => void;
  onRemoveRow: (index: number) => void;
}

export function StudentImportStep({
  step,
  fileInputRef,
  students,
  isUploading,
  onFileUpload,
  onProcessFile,
  onOpenPasteModal,
  onAddEmptyRow,
  onUpdateStudent,
  onRemoveRow,
}: StudentImportStepProps) {
  return (
    <div className={cn('p-6 border rounded-xl bg-card transition-all', step === 1 ? 'opacity-50 grayscale pointer-events-none' : 'opacity-100')}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs">2</span>
          Список студентов
        </h2>
        <div className="flex gap-2">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".xlsx,.xls,.docx,.txt,.csv"
            onChange={(event) => {
              void onFileUpload(event);
            }}
          />
          <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
            {isUploading ? 'Анализ...' : <><Upload className="w-4 h-4 mr-2" /> Импорт файла</>}
          </Button>
          <Button variant="outline" size="sm" onClick={onOpenPasteModal}>
            <ClipboardPaste className="w-4 h-4 mr-2" /> Вставить список
          </Button>
          <Button variant="secondary" size="sm" onClick={onAddEmptyRow}>
            <Plus className="w-4 h-4 mr-2" /> Добавить строку
          </Button>
        </div>
      </div>

      {students.length === 0 ? (
        <Dropzone
          onFileDrop={onProcessFile}
          isUploading={isUploading}
          accept=".xlsx,.xls,.docx,.txt,.csv"
          className="mb-4"
        />
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground font-medium">
              <tr>
                <th className="px-4 py-3 w-12">#</th>
                <th className="px-4 py-3">ФИО Студента</th>
                <th className="px-4 py-3 w-[100px] text-right">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {students.map((student, index) => (
                <tr key={index} className="group hover:bg-muted/30">
                  <td className="px-4 py-2 text-muted-foreground font-mono text-xs">{index + 1}</td>
                  <td className="px-4 py-2">
                    <input
                      className="w-full bg-transparent border-none focus:outline-none focus:ring-0 font-medium"
                      value={student.full_name}
                      onChange={(event) => onUpdateStudent(index, 'full_name', event.target.value)}
                      placeholder="Фамилия Имя Отчество"
                    />
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => onRemoveRow(index)}
                      className="p-1 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-2 text-xs text-muted-foreground flex items-center justify-between">
        <span>Всего студентов: {students.length}</span>
        <span>Поддерживается: .xlsx, .docx, .txt (список по строкам)</span>
      </div>
    </div>
  );
}
