'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/sonner';
import { GroupsAPI, StudentImport } from '@/lib/api';
import { parseStudentImports } from '../lib/studentImport';
import { GroupBasicsStep } from './_components/GroupBasicsStep';
import { StudentImportStep } from './_components/StudentImportStep';
import { GroupCreationSidebar } from './_components/GroupCreationSidebar';
import { StudentsPasteDialog } from './_components/StudentsPasteDialog';

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
    } catch {
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

  const handlePasteSubmit = () => {
    const newStudents = parseStudentImports(pasteText);
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
    } catch {
      toast.error('Ошибка при создании группы. Возможно, код уже занят.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-8">
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
        <div className="space-y-8">
          <GroupBasicsStep
            step={step}
            groupName={groupName}
            groupCode={groupCode}
            onGroupNameChange={setGroupName}
            onGroupCodeChange={setGroupCode}
          />
          <StudentImportStep
            step={step}
            fileInputRef={fileInputRef}
            students={students}
            isUploading={isUploading}
            onFileUpload={handleFileUpload}
            onProcessFile={processFile}
            onOpenPasteModal={() => setShowPasteModal(true)}
            onAddEmptyRow={addEmptyRow}
            onUpdateStudent={updateStudent}
            onRemoveRow={removeRow}
          />
        </div>

        <GroupCreationSidebar
          step={step}
          groupName={groupName}
          groupCode={groupCode}
          studentsCount={students.length}
          isSubmitting={isSubmitting}
          onNext={() => setStep(2)}
          onBack={() => setStep(1)}
          onSubmit={handleSubmit}
        />
      </div>

      <StudentsPasteDialog
        open={showPasteModal}
        text={pasteText}
        onTextChange={setPasteText}
        onClose={() => {
          setShowPasteModal(false);
          setPasteText('');
        }}
        onSubmit={handlePasteSubmit}
      />
    </div>
  );
}
