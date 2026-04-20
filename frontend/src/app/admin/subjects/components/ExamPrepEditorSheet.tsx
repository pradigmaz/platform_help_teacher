'use client';

import { useEffect, useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, Loader2, Plus, Save, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import LectureEditor from '@/components/lectures/LectureEditor';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { SubjectsAPI, type ExamPrepQuestion, type GroupSubjectOffering } from '@/lib/api';
import {
  createEmptyExamPrepQuestion,
  getExamPrepText,
  hasExamPrepContent,
  moveExamPrepQuestion,
  toExamPrepContentValue,
  toExamPrepEditorState,
} from '@/lib/utils/exam-prep';

interface ExamPrepEditorSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  offering: GroupSubjectOffering | null;
  onSaved: (questionsCount: number) => void;
}

function getQuestionPreview(question: ExamPrepQuestion, index: number) {
  const text = getExamPrepText(question.prompt);
  return text ? `Вопрос ${index + 1}: ${text}` : `Вопрос ${index + 1}`;
}

export function ExamPrepEditorSheet({
  open,
  onOpenChange,
  offering,
  onSaved,
}: ExamPrepEditorSheetProps) {
  const [questions, setQuestions] = useState<ExamPrepQuestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open || !offering) {
      return;
    }

    let cancelled = false;
    const loadQuestions = async () => {
      setQuestions([]);
      setLoading(true);
      try {
        const response = await SubjectsAPI.getExamPrep(offering.id);
        if (!cancelled) {
          setQuestions(response.questions);
        }
      } catch {
        if (!cancelled) {
          toast.error('Не удалось загрузить экзаменационные вопросы');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadQuestions();

    return () => {
      cancelled = true;
    };
  }, [offering, open]);

  const questionsCountLabel = useMemo(
    () => `${questions.length} ${questions.length === 1 ? 'вопрос' : questions.length < 5 ? 'вопроса' : 'вопросов'}`,
    [questions.length],
  );

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
    if (!offering) {
      return;
    }

    const invalidQuestion = questions.find((question) => !hasExamPrepContent(question.prompt));
    if (invalidQuestion) {
      toast.error('У каждого вопроса должен быть непустой текст');
      return;
    }

    setSaving(true);
    try {
      const payload = questions.map((question) => ({
        id: question.id,
        prompt:
          typeof question.prompt === 'string'
            ? question.prompt.trim()
            : {
                text: getExamPrepText(question.prompt),
                content: toExamPrepEditorState(question.prompt) as unknown as Record<string, unknown>,
              },
        answer: hasExamPrepContent(question.answer)
          ? typeof question.answer === 'string'
            ? question.answer.trim()
            : {
                text: getExamPrepText(question.answer),
                content: toExamPrepEditorState(question.answer) as unknown as Record<string, unknown>,
              }
          : null,
      }));

      const response = await SubjectsAPI.updateExamPrep(offering.id, payload);
      setQuestions(response.questions);
      onSaved(response.questions_count);
      toast.success('Экзаменационные вопросы сохранены');
    } catch {
      toast.error('Не удалось сохранить экзаменационные вопросы');
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
              <SheetTitle>
                Вопросы к экзамену{offering ? `: ${offering.group_name} / ${offering.subject_name}` : ''}
              </SheetTitle>
              <SheetDescription>
                Банк вопросов хранится на уровне конкретной связки группа / предмет / семестр и используется в student-режимах «Вопросы», «Карточки» и «Квиз».
              </SheetDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">Экзамен</Badge>
              {offering ? <Badge variant="outline">{offering.semester}</Badge> : null}
              <Badge variant="outline">{questionsCountLabel}</Badge>
            </div>
          </div>
        </SheetHeader>

        <div className="flex items-center justify-between border-b border-border/60 px-6 py-4">
          <div className="text-sm text-muted-foreground">
            Можно оставить только вопрос. Ответ опционален: в student-режиме это будет self-check без эталона.
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => setQuestions((current) => [...current, createEmptyExamPrepQuestion()])}
          >
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
                  Вопросов пока нет. Добавьте первый вопрос для этой экзаменационной связки.
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
          <div className="text-sm text-muted-foreground">Сохранение обновит student-режимы без отдельной публикации.</div>
          <Button type="button" onClick={handleSave} disabled={saving || loading || !offering}>
            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            Сохранить
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
