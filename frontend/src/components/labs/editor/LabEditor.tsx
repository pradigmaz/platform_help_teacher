'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { IconTarget, IconBook, IconCode, IconQuestionMark } from '@tabler/icons-react';
import { cn } from '@/lib/utils';
import { LabData, LabVariant, LabEditorProps } from './types';
import { HeaderTab } from './HeaderTab';
import { TheoryTab } from './TheoryTab';
import { PracticeTab } from './PracticeTab';
import { QuestionsTab } from './QuestionsTab';
import { LabStyleProvider, useLabStyle } from './LabStyleContext';

const DEFAULT_FORMATTING = '1. Тема и цель работы\n2. Краткая теория\n3. Код решения\n4. Скриншоты результатов\n5. Ответы на контрольные вопросы';

function LabEditorInner({ initialData, onSave, className }: LabEditorProps) {
  const { style, setFontSize, setLineHeight } = useLabStyle();
  const [data, setData] = useState<LabData>({
    number: initialData?.number || 1,
    title: initialData?.title || '',
    goal: initialData?.goal || '',
    formatting_guide: initialData?.formatting_guide || DEFAULT_FORMATTING,
    theory_content: initialData?.theory_content,
    practice_content: initialData?.practice_content,
    variants: initialData?.variants || [{ number: 1, description: '', test_data: '' }],
    questions: initialData?.questions || [''],
    max_grade: 5,
    deadline_5_lessons: initialData?.deadline_5_lessons,
    deadline_4_lessons: initialData?.deadline_4_lessons,
    is_sequential: initialData?.is_sequential ?? true,
    ...initialData,
  });

  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('header');

  const updateField = <K extends keyof LabData>(field: K, value: LabData[K]) => {
    setData(prev => ({ ...prev, [field]: value }));
  };

  // Variants
  const addVariant = () => {
    setData(prev => ({
      ...prev,
      variants: [...prev.variants, { number: prev.variants.length + 1, description: '', test_data: '' }],
    }));
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
  const addQuestion = () => setData(prev => ({ ...prev, questions: [...prev.questions, ''] }));
  const updateQuestion = (index: number, value: string) => {
    setData(prev => ({ ...prev, questions: prev.questions.map((q, i) => i === index ? value : q) }));
  };
  const removeQuestion = (index: number) => {
    setData(prev => ({ ...prev, questions: prev.questions.filter((_, i) => i !== index) }));
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

        <TabsContent value="header"><HeaderTab data={data} updateField={updateField} /></TabsContent>
        <TabsContent value="theory">
          <TheoryTab 
            content={data.theory_content} 
            onChange={(c) => updateField('theory_content', c)}
            onFontSizeChange={setFontSize}
            onLineHeightChange={setLineHeight}
          />
        </TabsContent>
        <TabsContent value="practice">
          <PracticeTab
            practiceContent={data.practice_content}
            variants={data.variants}
            onPracticeChange={(c) => updateField('practice_content', c)}
            onAddVariant={addVariant}
            onUpdateVariant={updateVariant}
            onRemoveVariant={removeVariant}
            onMoveVariant={moveVariant}
            externalFontSize={style.fontSize}
            externalLineHeight={style.lineHeight}
          />
        </TabsContent>
        <TabsContent value="questions">
          <QuestionsTab questions={data.questions} onAdd={addQuestion} onUpdate={updateQuestion} onRemove={removeQuestion} />
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
