'use client';

import { useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { IconTarget, IconBook, IconCode, IconQuestionMark } from '@tabler/icons-react';
import { cn } from '@/lib/utils';
import { LabData, LabVariant, LabEditorProps, LabQuestion, createVariant, createQuestion, normalizeVariant, normalizeQuestion } from './types';
import { HeaderTab } from './HeaderTab';
import { LabStyleProvider, useLabStyle } from './LabStyleContext';

const DEFAULT_FORMATTING = '1. Тема и цель работы\n2. Краткая теория\n3. Код решения\n4. Скриншоты результатов\n5. Ответы на контрольные вопросы';

function EditorTabSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("space-y-4", className)}>
      <Skeleton className="h-10 w-56" />
      <Skeleton className="h-24 rounded-xl" />
      <Skeleton className="h-[420px] rounded-xl" />
    </div>
  );
}

const TheoryTab = dynamic(() => import('./TheoryTab').then((module) => module.TheoryTab), {
  ssr: false,
  loading: () => <EditorTabSkeleton />,
});

const PracticeTab = dynamic(() => import('./PracticeTab').then((module) => module.PracticeTab), {
  ssr: false,
  loading: () => <EditorTabSkeleton />,
});

const QuestionsTab = dynamic(() => import('./QuestionsTab').then((module) => module.QuestionsTab), {
  ssr: false,
  loading: () => <EditorTabSkeleton className="min-h-[420px]" />,
});

function LabEditorInner({ initialData, onSave, className }: LabEditorProps) {
  const { style, setFontSize, setLineHeight } = useLabStyle();
  
  // Нормализуем начальные данные с ID
  const normalizedVariants = (initialData?.variants || []).map((v, i) => 
    normalizeVariant({ ...v, number: v.number || i + 1 })
  );
  const normalizedQuestions = (initialData?.questions || []).map(normalizeQuestion);
  
  const [data, setData] = useState<LabData>(() => ({
    id: initialData?.id,
    number: initialData?.number || 1,
    title: initialData?.title || '',
    goal: initialData?.goal || '',
    formatting_guide: initialData?.formatting_guide || DEFAULT_FORMATTING,
    theory_content: initialData?.theory_content,
    practice_content: initialData?.practice_content,
    variants: normalizedVariants.length > 0 ? normalizedVariants : [createVariant(1)],
    questions: normalizedQuestions.length > 0 ? normalizedQuestions : [createQuestion()],
    max_grade: 5,
    deadline_5_lessons: initialData?.deadline_5_lessons,
    deadline_4_lessons: initialData?.deadline_4_lessons,
    is_sequential: initialData?.is_sequential ?? true,
    subject_id: initialData?.subject_id,
  }));

  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('header');

  const updateField = <K extends keyof LabData>(field: K, value: LabData[K]) => {
    setData(prev => ({ ...prev, [field]: value }));
  };

  // Variants
  const setVariantsCount = (count: number) => {
    setData(prev => {
      const currentCount = prev.variants.length;
      if (count === currentCount) return prev;
      
      if (count > currentCount) {
        const newVariants = [...prev.variants];
        for (let i = currentCount; i < count; i++) {
          newVariants.push(createVariant(i + 1));
        }
        return { ...prev, variants: newVariants };
      } else {
        return { ...prev, variants: prev.variants.slice(0, count) };
      }
    });
  };

  const updateVariant = (index: number, field: keyof LabVariant, value: unknown) => {
    setData(prev => ({
      ...prev,
      variants: prev.variants.map((v, i) => i === index ? { ...v, [field]: value } : v),
    }));
  };

  const removeVariant = (index: number) => {
    setData(prev => ({
      ...prev,
      variants: prev.variants.filter((_, i) => i !== index).map((v, i) => ({ ...v, number: i + 1 })),
    }));
  };

  const moveVariant = (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= data.variants.length) return;
    setData(prev => {
      const newVariants = [...prev.variants];
      [newVariants[index], newVariants[targetIndex]] = [newVariants[targetIndex], newVariants[index]];
      return { ...prev, variants: newVariants.map((v, i) => ({ ...v, number: i + 1 })) };
    });
  };

  // Questions
  const addQuestion = () => setData(prev => ({ ...prev, questions: [...prev.questions, createQuestion()] }));
  const updateQuestion = (index: number, value: LabQuestion) => {
    setData(prev => ({ ...prev, questions: prev.questions.map((q, i) => i === index ? value : q) }));
  };
  const removeQuestion = (index: number) => {
    setData(prev => ({ ...prev, questions: prev.questions.filter((_, i) => i !== index) }));
  };
  const moveQuestion = (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= data.questions.length) return;
    setData(prev => {
      const newQuestions = [...prev.questions];
      [newQuestions[index], newQuestions[targetIndex]] = [newQuestions[targetIndex], newQuestions[index]];
      return { ...prev, questions: newQuestions };
    });
  };

  const handleSave = useCallback(async () => {
    if (!data.title.trim()) { alert('Укажите название лабораторной'); return; }
    setSaving(true);
    try { await onSave(data); } finally { setSaving(false); }
  }, [data, onSave]);

  return (
    <div className={cn("space-y-6", className)}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            {initialData?.id ? 'Редактирование лабораторной' : 'Новая лабораторная работа'}
          </h1>
          <p className="text-muted-foreground">Заполните все 4 секции</p>
        </div>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Сохранение...' : 'Сохранить'}
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="header" className="gap-2"><IconTarget className="h-4 w-4" />Шапка</TabsTrigger>
          <TabsTrigger value="theory" className="gap-2"><IconBook className="h-4 w-4" />Теория</TabsTrigger>
          <TabsTrigger value="practice" className="gap-2"><IconCode className="h-4 w-4" />Практика</TabsTrigger>
          <TabsTrigger value="questions" className="gap-2"><IconQuestionMark className="h-4 w-4" />Вопросы</TabsTrigger>
        </TabsList>

        <TabsContent value="header">
          <HeaderTab data={data} updateField={updateField} />
        </TabsContent>
        <TabsContent value="theory">
          {activeTab === 'theory' ? (
            <TheoryTab 
              content={data.theory_content} 
              onChange={(c) => updateField('theory_content', c)}
              onFontSizeChange={setFontSize}
              onLineHeightChange={setLineHeight}
            />
          ) : null}
        </TabsContent>
        <TabsContent value="practice">
          {activeTab === 'practice' ? (
            <PracticeTab
              practiceContent={data.practice_content}
              variants={data.variants}
              onPracticeChange={(c) => updateField('practice_content', c)}
              onSetVariantsCount={setVariantsCount}
              onUpdateVariant={updateVariant}
              onRemoveVariant={removeVariant}
              onMoveVariant={moveVariant}
              externalFontSize={style.fontSize}
              externalLineHeight={style.lineHeight}
            />
          ) : null}
        </TabsContent>
        <TabsContent value="questions">
          {activeTab === 'questions' ? (
            <QuestionsTab 
              questions={data.questions} 
              onAdd={addQuestion} 
              onUpdate={updateQuestion} 
              onRemove={removeQuestion}
              onMove={moveQuestion}
              externalFontSize={style.fontSize}
              externalLineHeight={style.lineHeight}
            />
          ) : null}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default LabEditor;

export function LabEditor(props: LabEditorProps) {
  return (
    <LabStyleProvider>
      <LabEditorInner {...props} />
    </LabStyleProvider>
  );
}
