'use client';

import { useEffect, useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, Loader2, Plus, Save, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import LectureEditor from '@/components/lectures/LectureEditor';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { ExamBanksAPI, type AdminExamQuestionBankDetail, type ExamPrepQuestion } from '@/lib/api';
import {
  createEmptyExamPrepQuestion,
  getExamPrepText,
  hasExamPrepContent,
  moveExamPrepQuestion,
  toExamPrepContentValue,
  toExamPrepEditorState,
} from '@/lib/utils/exam-prep';

interface ExamQuestionBankEditorSheetProps {
  open: boolean;
  bankId: string | null;
  onOpenChange: (open: boolean) => void;
  onSaved: (bank: AdminExamQuestionBankDetail) => void;
}

function getQuestionPreview(question: ExamPrepQuestion, index: number) {
  const text = getExamPrepText(question.prompt);
  return text ? `Вопрос ${index + 1}: ${text}` : `Вопрос ${index + 1}`;
}

function formatQuestionCount(count: number) {
  if (count === 1) {
    return '1 вопрос';
  }
  if (count < 5) {
    return `${count} вопроса`;
  }
  return `${count} вопросов`;
}

export function ExamQuestionBankEditorSheet({
  open,
  bankId,
  onOpenChange,
  onSaved,
}: ExamQuestionBankEditorSheetProps) {
  const [bank, setBank] = useState<AdminExamQuestionBankDetail | null>(null);
  const [questions, setQuestions] = useState<ExamPrepQuestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open || !bankId) {
      setBank(null);
      setQuestions([]);
      setLoading(false);
      return;
    }

    let cancelled = false;
    const loadBank = async () => {
      setBank(null);
      setLoading(true);
      setQuestions([]);
      try {
        const response = await ExamBanksAPI.getBank(bankId);
        if (!cancelled) {
          setBank(response);
          setQuestions(response.questions);
        }
      } catch {
        if (!cancelled) {
          setBank(null);
          setQuestions([]);
          toast.error('Не удалось загрузить банк вопросов');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadBank();
    return () => {
      cancelled = true;
    };
  }, [bankId, open]);

  const groupsLabel = useMemo(() => {
    if (!bank) {
      return '';
    }
    return bank.offerings.map((offering) => offering.group_name).join(', ');
  }, [bank]);

  function updateQuestion(index: number, nextQuestion: ExamPrepQuestion) {
    setQuestions((current) => current.map((question, questionIndex) => (questionIndex === index ? nextQuestion : question)));
  }

  function handleSaveContent(index: number, field: 'prompt' | 'answer', content: Record<string, unknown>) {
    const nextValue = toExamPrepContentValue(content);
    const question = questions[index];
    if (!question) {
      return;
    }
    updateQuestion(index, {
      ...question,
      [field]: field === 'answer' && !hasExamPrepContent(nextValue) ? null : nextValue,
    });
  }

  async function handleSave() {
    if (!bankId || !bank || bank.bank_id !== bankId) {
      return;
    }
    if (questions.some((question) => !hasExamPrepContent(question.prompt))) {
      toast.error('У каждого вопроса должен быть непустой текст');
      return;
    }

    setSaving(true);
    try {
      const response = await ExamBanksAPI.updateBank(bankId, questions);
      setBank(response);
      setQuestions(response.questions);
      onSaved(response);
      toast.success('Банк вопросов сохранён');
    } catch {
      toast.error('Не удалось сохранить банк вопросов');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col gap-0 overflow-hidden p-0 sm:max-w-5xl">
        <SheetHeader className="border-b border-border/60 px-6 py-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <SheetTitle>{bank ? `Банк вопросов: ${bank.subject_name}` : 'Банк вопросов'}</SheetTitle>
              <SheetDescription>
                {bank
                  ? `Семестр ${bank.semester}. Банк сейчас используют группы: ${groupsLabel || '—'}.`
                  : 'Загрузка банка вопросов…'}
              </SheetDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              {bank ? <Badge variant="outline">{bank.semester}</Badge> : null}
              <Badge variant="outline">{formatQuestionCount(questions.length)}</Badge>
            </div>
          </div>
        </SheetHeader>

        <div className="flex items-center justify-between border-b border-border/60 px-6 py-4">
          <div className="text-sm text-muted-foreground">
            Один банк используется сразу несколькими группами. Изменение вопросов обновит все привязанные связки.
          </div>
          <Button type="button" variant="outline" onClick={() => setQuestions((current) => [...current, createEmptyExamPrepQuestion()])}>
            <Plus className="mr-2 h-4 w-4" />
            Добавить вопрос
          </Button>
        </div>

        {loading ? (
          <div className="px-6 py-10 text-center text-sm text-muted-foreground">Загрузка вопросов…</div>
        ) : (
          <ScrollArea className="flex-1">
            <div className="space-y-4 px-6 py-5">
              {!questions.length ? (
                <div className="rounded-2xl border border-dashed border-border/60 bg-muted/20 p-8 text-center text-sm text-muted-foreground">
                  Вопросов пока нет. Добавьте первый вопрос для этого банка.
                </div>
              ) : null}

              {questions.map((question, index) => (
                <div key={question.id} className="space-y-4 rounded-2xl border border-border/60 bg-background/90 p-4">
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div className="space-y-1">
                      <div className="text-sm font-semibold text-foreground">{getQuestionPreview(question, index)}</div>
                      <div className="text-xs text-muted-foreground">
                        Ответ {hasExamPrepContent(question.answer) ? 'заполнен' : 'не заполнен'}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        disabled={index === 0}
                        onClick={() => setQuestions((current) => moveExamPrepQuestion(current, index, -1))}
                      >
                        <ArrowUp className="h-4 w-4" />
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        disabled={index === questions.length - 1}
                        onClick={() => setQuestions((current) => moveExamPrepQuestion(current, index, 1))}
                      >
                        <ArrowDown className="h-4 w-4" />
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={() => setQuestions((current) => current.filter((item) => item.id !== question.id))}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-sm font-medium text-foreground">Вопрос</div>
                    <LectureEditor
                      initialContent={toExamPrepEditorState(question.prompt)}
                      onChange={(content) => handleSaveContent(index, 'prompt', content as unknown as Record<string, unknown>)}
                      preset="minimal"
                      stickyToolbar={false}
                      placeholder="Сформулируйте вопрос для подготовки к экзамену"
                      className="shadow-none"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="text-sm font-medium text-foreground">Ответ / ориентир</div>
                    <LectureEditor
                      initialContent={toExamPrepEditorState(question.answer)}
                      onChange={(content) => handleSaveContent(index, 'answer', content as unknown as Record<string, unknown>)}
                      preset="minimal"
                      stickyToolbar={false}
                      placeholder="Опционально: краткий ответ или эталонная формулировка"
                      className="shadow-none"
                    />
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}

        <div className="flex items-center justify-between border-t border-border/60 px-6 py-4">
          <div className="text-sm text-muted-foreground">Сохранение обновит student-режимы для всех привязанных групп.</div>
          <Button type="button" onClick={handleSave} disabled={saving || loading || !bankId || !bank || bank.bank_id !== bankId}>
            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            Сохранить
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
