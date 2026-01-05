'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Upload, FileText, Check, X, Plus, ClipboardPaste } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/sonner';
import { GroupsAPI, StudentImport } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Dropzone } from '@/components/animate-ui/dropzone';

export default function CreateGroupPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // State формы
  const [step, setStep] = useState<1 | 2>(1);
  const [groupName, setGroupName] = useState('');
  const [groupCode, setGroupCode] = useState('');
  const [students, setStudents] = useState<StudentImport[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPasteModal, setShowPasteModal] = useState(false);
  const [pasteText, setPasteText] = useState('');

  // Обработчик загрузки файла
  const processFile = async (file: File) => {
    setIsUploading(true);
    try {
      const parsedData = await GroupsAPI.parseFile(file);
      if (process.env.NODE_ENV === 'development') {
        console.log('Parsed data:', parsedData);
      }
      setStudents(prev => [...prev, ...parsedData]);
      toast.success('Файл успешно прочитан');
    } catch (err) {
      toast.error('Ошибка при чтении файла. Убедитесь, что это Excel, Word или TXT.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await processFile(file);
  };

  // Парсинг вставленного текста
  const handlePasteSubmit = () => {
    const lines = pasteText.split('\n').map(line => line.trim()).filter(Boolean);
    const newStudents: StudentImport[] = [];
    
    for (const line of lines) {
      // Убираем нумерацию (1. или 1) в начале)
      const cleaned = line.replace(/^\d+[\.\)\s]+/, '').trim();
      // Убираем лишние пробелы, оставляем только буквы и пробелы
      const name = cleaned.replace(/[^\p{L}\s-]/gu, ' ').replace(/\s+/g, ' ').trim();
      
      if (name && name.split(' ').length >= 2) {
        newStudents.push({ full_name: name });
      }
    }
    
    if (newStudents.length > 0) {
      setStudents(prev => [...prev, ...newStudents]);
      setPasteText('');
      setShowPasteModal(false);
      toast.success(`Добавлено студентов: ${newStudents.length}`);
    } else {
      toast.error('Не удалось распознать имена. Убедитесь, что каждое ФИО на отдельной строке.');
    }
  };

  // Добавление пустой строки
  const addEmptyRow = () => {
    setStudents([...students, { full_name: '' }]);
  };

  // Редактирование ячейки
  const updateStudent = (index: number, field: keyof StudentImport, value: string) => {
    const newStudents = [...students];
    newStudents[index] = { ...newStudents[index], [field]: value };
    setStudents(newStudents);
  };

  // Удаление строки
  const removeRow = (index: number) => {
    setStudents(students.filter((_, i) => i !== index));
  };

  // Финальная отправка
  const handleSubmit = async () => {
    if (!groupName || !groupCode) {
      toast.error('Заполните название и код группы');
      return;
    }
    const validStudents = students.filter(s => s.full_name.trim().length > 0);
    
    setIsSubmitting(true);
    try {
      await GroupsAPI.create({
        name: groupName,
        code: groupCode,
        students: validStudents
      });
      toast.success('Группа успешно создана');
      router.push('/admin/groups');
    } catch (e) {
      toast.error('Ошибка при создании группы. Возможно, код уже занят.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Создание новой группы</h1>
          <p className="text-muted-foreground">Шаг {step} из 2</p>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[1fr_300px]">
        
        {/* Main Content */}
        <div className="space-y-8">
          
          {/* STEP 1: Basic Info */}
          <div className={cn("p-6 border rounded-xl bg-card", step !== 1 && "opacity-50 pointer-events-none")}>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs">1</span>
              Основные данные
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Название группы</label>
                <input
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  placeholder="Например: ИС-24-1"
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Код группы</label>
                <div className="flex gap-2">
                  <input
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder="IS-24-1"
                    value={groupCode}
                    onChange={(e) => setGroupCode(e.target.value.toUpperCase())}
                  />
                </div>
                <p className="text-xs text-muted-foreground">Уникальный код группы для идентификации.</p>
              </div>
            </div>
          </div>

          {/* STEP 2: Students Import */}
          <div className={cn("p-6 border rounded-xl bg-card transition-all", step === 1 ? "opacity-50 grayscale pointer-events-none" : "opacity-100")}>
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
                  onChange={handleFileUpload}
                />
                <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
                  {isUploading ? "Анализ..." : <><Upload className="w-4 h-4 mr-2" /> Импорт файла</>}
                </Button>
                <Button variant="outline" size="sm" onClick={() => setShowPasteModal(true)}>
                  <ClipboardPaste className="w-4 h-4 mr-2" /> Вставить список
                </Button>
                <Button variant="secondary" size="sm" onClick={addEmptyRow}>
                  <Plus className="w-4 h-4 mr-2" /> Добавить строку
                </Button>
              </div>
            </div>

            {/* Editable Table or Dropzone */}
            {students.length === 0 ? (
              <Dropzone
                onFileDrop={processFile}
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
                    {students.map((student, idx) => (
                      <tr key={idx} className="group hover:bg-muted/30">
                        <td className="px-4 py-2 text-muted-foreground font-mono text-xs">{idx + 1}</td>
                        <td className="px-4 py-2">
                          <input
                            className="w-full bg-transparent border-none focus:outline-none focus:ring-0 font-medium"
                            value={student.full_name}
                            onChange={(e) => updateStudent(idx, 'full_name', e.target.value)}
                            placeholder="Фамилия Имя Отчество"
                          />
                        </td>
                        <td className="px-4 py-2 text-right">
                          <button 
                            onClick={() => removeRow(idx)}
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

        </div>

        {/* Sidebar Actions */}
        <div className="space-y-4">
          <div className="sticky top-8 space-y-4">
            <div className="p-4 border rounded-xl bg-card">
              <h3 className="font-semibold mb-2">Статус</h3>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  {groupName && groupCode ? <Check className="w-4 h-4 text-green-500" /> : <div className="w-4 h-4 border rounded-full" />}
                  Данные группы
                </li>
                <li className="flex items-center gap-2">
                  {students.length > 0 ? <Check className="w-4 h-4 text-green-500" /> : <div className="w-4 h-4 border rounded-full" />}
                  Студенты ({students.length})
                </li>
              </ul>
            </div>

            {step === 1 ? (
              <Button 
                className="w-full" 
                size="lg"
                disabled={!groupName || !groupCode}
                onClick={() => setStep(2)}
              >
                Далее: Студенты
              </Button>
            ) : (
              <div className="space-y-2">
                <Button 
                  className="w-full bg-green-600 hover:bg-green-700" 
                  size="lg"
                  disabled={students.length === 0 || isSubmitting}
                  onClick={handleSubmit}
                >
                  {isSubmitting ? 'Создание...' : 'Сохранить группу'}
                </Button>
                <Button variant="outline" className="w-full" onClick={() => setStep(1)}>
                  Назад
                </Button>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Paste Modal */}
      {showPasteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card border rounded-xl p-6 w-full max-w-lg mx-4">
            <h3 className="text-lg font-semibold mb-4">Вставить список студентов</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Вставьте список ФИО, каждое имя на новой строке. Нумерация будет удалена автоматически.
            </p>
            <textarea
              className="w-full h-64 p-3 border rounded-lg bg-background text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="1. Иванов Иван Иванович&#10;2. Петров Пётр Петрович&#10;3. Сидорова Анна Сергеевна"
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              autoFocus
            />
            <div className="flex gap-2 mt-4">
              <Button variant="outline" className="flex-1" onClick={() => { setShowPasteModal(false); setPasteText(''); }}>
                Отмена
              </Button>
              <Button className="flex-1" onClick={handlePasteSubmit} disabled={!pasteText.trim()}>
                Добавить
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
