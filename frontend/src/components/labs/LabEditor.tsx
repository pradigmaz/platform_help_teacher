'use client';

import React, { useState, useCallback } from 'react';
import { SerializedEditorState } from 'lexical';
import { LectureEditor } from '@/components/lectures';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { IconTarget, IconBook, IconCode, IconQuestionMark, IconPlus, IconTrash, IconGripVertical } from '@tabler/icons-react';
import { cn } from '@/lib/utils';

export interface LabVariant {
  number: number;
  description: string;
  test_data?: string;
}

export interface LabData {
  id?: string;
  number: number;
  title: string;
  topic?: string;
  goal?: string;
  formatting_guide?: string;
  theory_content?: SerializedEditorState;
  practice_content?: SerializedEditorState;
  variants: LabVariant[];
  questions: string[];
  max_grade: number;
  deadline?: string;
  is_sequential: boolean;
}

interface LabEditorProps {
  initialData?: Partial<LabData>;
  onSave: (data: LabData) => Promise<void>;
  className?: string;
}

export function LabEditor({ initialData, onSave, className }: LabEditorProps) {
  const [data, setData] = useState<LabData>({
    number: initialData?.number || 1,
    title: initialData?.title || '',
    topic: initialData?.topic || '',
    goal: initialData?.goal || '',
    formatting_guide: initialData?.formatting_guide || '1. Тема и цель работы\n2. Краткая теория\n3. Код решения\n4. Скриншоты результатов\n5. Ответы на контрольные вопросы',
    theory_content: initialData?.theory_content,
    practice_content: initialData?.practice_content,
    variants: initialData?.variants || [{ number: 1, description: '', test_data: '' }],
    questions: initialData?.questions || [''],
    max_grade: initialData?.max_grade || 5,
    deadline: initialData?.deadline,
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
    const newNumber = data.variants.length + 1;
    setData(prev => ({
      ...prev,
      variants: [...prev.variants, { number: newNumber, description: '', test_data: '' }],
    }));
  };

  const updateVariant = (index: number, field: keyof LabVariant, value: string | number) => {
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

  // Questions
  const addQuestion = () => {
    setData(prev => ({ ...prev, questions: [...prev.questions, ''] }));
  };

  const updateQuestion = (index: number, value: string) => {
    setData(prev => ({
      ...prev,
      questions: prev.questions.map((q, i) => i === index ? value : q),
    }));
  };

  const removeQuestion = (index: number) => {
    setData(prev => ({
      ...prev,
      questions: prev.questions.filter((_, i) => i !== index),
    }));
  };

  const handleSave = useCallback(async () => {
    if (!data.title.trim()) {
      alert('Укажите название лабораторной');
      return;
    }
    setSaving(true);
    try {
      await onSave(data);
    } finally {
      setSaving(false);
    }
  }, [data, onSave]);

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header with save button */}
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

      {/* Tabs for sections */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="header" className="gap-2">
            <IconTarget className="h-4 w-4" />
            Шапка
          </TabsTrigger>
          <TabsTrigger value="theory" className="gap-2">
            <IconBook className="h-4 w-4" />
            Теория
          </TabsTrigger>
          <TabsTrigger value="practice" className="gap-2">
            <IconCode className="h-4 w-4" />
            Практика
          </TabsTrigger>
          <TabsTrigger value="questions" className="gap-2">
            <IconQuestionMark className="h-4 w-4" />
            Вопросы
          </TabsTrigger>
        </TabsList>

        {/* Section 1: Header */}
        <TabsContent value="header" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <IconTarget className="h-5 w-5" />
                Шапка лабораторной
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Номер лабы</label>
                  <Input
                    type="number"
                    min={1}
                    value={data.number}
                    onChange={(e) => updateField('number', Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Макс. оценка</label>
                  <Input
                    type="number"
                    min={1}
                    max={10}
                    value={data.max_grade}
                    onChange={(e) => updateField('max_grade', Number(e.target.value))}
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium">Название *</label>
                <Input
                  value={data.title}
                  onChange={(e) => updateField('title', e.target.value)}
                  placeholder="Unit-тестирование в C#"
                />
              </div>

              <div>
                <label className="text-sm font-medium">Тема</label>
                <Input
                  value={data.topic || ''}
                  onChange={(e) => updateField('topic', e.target.value)}
                  placeholder="Основы NUnit"
                />
              </div>

              <div>
                <label className="text-sm font-medium">Цель работы</label>
                <Textarea
                  value={data.goal || ''}
                  onChange={(e) => updateField('goal', e.target.value)}
                  placeholder="Научиться писать unit-тесты..."
                  rows={3}
                />
              </div>

              <div>
                <label className="text-sm font-medium">Что записать в тетрадь</label>
                <Textarea
                  value={data.formatting_guide || ''}
                  onChange={(e) => updateField('formatting_guide', e.target.value)}
                  placeholder="1. Тема и цель работы..."
                  rows={5}
                />
              </div>

              <div>
                <label className="text-sm font-medium">Дедлайн</label>
                <Input
                  type="datetime-local"
                  value={data.deadline || ''}
                  onChange={(e) => updateField('deadline', e.target.value)}
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_sequential"
                  checked={data.is_sequential}
                  onChange={(e) => updateField('is_sequential', e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="is_sequential" className="text-sm">
                  Требуется сдача предыдущей лабы для доступа
                </label>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Section 2: Theory */}
        <TabsContent value="theory">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <IconBook className="h-5 w-5" />
                Теоретическая часть
              </CardTitle>
            </CardHeader>
            <CardContent>
              <LectureEditor
                initialContent={data.theory_content}
                onChange={(content) => updateField('theory_content', content)}
                className="min-h-[500px]"
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Section 3: Practice with Variants */}
        <TabsContent value="practice" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <IconCode className="h-5 w-5" />
                Общее задание
              </CardTitle>
            </CardHeader>
            <CardContent>
              <LectureEditor
                initialContent={data.practice_content}
                onChange={(content) => updateField('practice_content', content)}
                className="min-h-[300px]"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Варианты заданий</span>
                <Button size="sm" onClick={addVariant}>
                  <IconPlus className="h-4 w-4 mr-1" />
                  Добавить вариант
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {data.variants.map((variant, index) => (
                <div key={index} className="flex gap-4 p-4 rounded-lg border bg-muted/30">
                  <div className="flex items-center">
                    <IconGripVertical className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <Badge variant="secondary" className="h-8 w-8 flex items-center justify-center">
                    {variant.number}
                  </Badge>
                  <div className="flex-1 space-y-2">
                    <Input
                      value={variant.description}
                      onChange={(e) => updateVariant(index, 'description', e.target.value)}
                      placeholder="Описание варианта (напр. Сложение)"
                    />
                    <Textarea
                      value={variant.test_data || ''}
                      onChange={(e) => updateVariant(index, 'test_data', e.target.value)}
                      placeholder="Тестовые данные (напр. 2+2=4, -1+1=0)"
                      rows={2}
                    />
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeVariant(index)}
                    disabled={data.variants.length <= 1}
                  >
                    <IconTrash className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Section 4: Questions */}
        <TabsContent value="questions">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <IconQuestionMark className="h-5 w-5" />
                  Контрольные вопросы
                </span>
                <Button size="sm" onClick={addQuestion}>
                  <IconPlus className="h-4 w-4 mr-1" />
                  Добавить вопрос
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.questions.map((question, index) => (
                <div key={index} className="flex gap-3 items-start">
                  <Badge variant="outline" className="mt-2">{index + 1}</Badge>
                  <Textarea
                    value={question}
                    onChange={(e) => updateQuestion(index, e.target.value)}
                    placeholder="Введите вопрос..."
                    rows={2}
                    className="flex-1"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeQuestion(index)}
                    disabled={data.questions.length <= 1}
                  >
                    <IconTrash className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default LabEditor;
