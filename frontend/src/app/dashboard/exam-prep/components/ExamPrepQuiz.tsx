'use client';

import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, CircleHelp, RotateCcw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import type { ExamPrepQuestion } from '@/lib/api';
import { hasExamPrepContent, pickQuizQuestions } from '@/lib/utils/exam-prep';
import { ExamPrepContent } from './ExamPrepContent';

export function ExamPrepQuiz({ questions }: { questions: ExamPrepQuestion[] }) {
  const [sessionQuestions, setSessionQuestions] = useState<ExamPrepQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [stats, setStats] = useState({ known: 0, repeat: 0 });

  const currentQuestion = sessionQuestions[currentIndex] ?? null;
  const isFinished = sessionQuestions.length > 0 && currentIndex >= sessionQuestions.length;
  const progressValue = sessionQuestions.length ? Math.round((Math.min(currentIndex, sessionQuestions.length) / sessionQuestions.length) * 100) : 0;

  const sessionSizeLabel = useMemo(() => {
    if (!sessionQuestions.length) {
      return 'Нет вопросов';
    }
    return `${sessionQuestions.length} ${sessionQuestions.length === 1 ? 'вопрос' : sessionQuestions.length < 5 ? 'вопроса' : 'вопросов'}`;
  }, [sessionQuestions.length]);

  function startSession() {
    setSessionQuestions(pickQuizQuestions(questions, 10));
    setCurrentIndex(0);
    setShowAnswer(false);
    setStats({ known: 0, repeat: 0 });
  }

  useEffect(() => {
    startSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questions]);

  function answerCurrent(result: 'known' | 'repeat') {
    setStats((current) => ({ ...current, [result]: current[result] + 1 }));
    setCurrentIndex((current) => current + 1);
    setShowAnswer(false);
  }

  return (
    <Card className="border-border/60 bg-background/80 shadow-sm">
      <CardHeader className="space-y-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <CardTitle className="flex items-center gap-2 text-xl">
              <CircleHelp className="h-5 w-5 text-primary" />
              Квиз
            </CardTitle>
            <div className="text-sm text-muted-foreground">
              Сессия собирается случайно: до 10 вопросов, по одному на экран, с быстрой self-check обратной связью.
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">{sessionSizeLabel}</Badge>
            <Badge variant="outline">Знаю: {stats.known}</Badge>
            <Badge variant="outline">Повторить: {stats.repeat}</Badge>
          </div>
        </div>
        <Progress value={progressValue} className="h-2" />
      </CardHeader>
      <CardContent>
        {isFinished ? (
          <div className="space-y-4 rounded-2xl border border-border/60 bg-muted/20 p-6">
            <div className="text-lg font-semibold text-foreground">Сессия завершена</div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-border/60 bg-background p-4">
                <div className="text-sm text-muted-foreground">Знаю</div>
                <div className="mt-2 text-3xl font-bold text-foreground">{stats.known}</div>
              </div>
              <div className="rounded-xl border border-border/60 bg-background p-4">
                <div className="text-sm text-muted-foreground">Повторить</div>
                <div className="mt-2 text-3xl font-bold text-foreground">{stats.repeat}</div>
              </div>
            </div>
            <Button type="button" onClick={startSession}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Начать заново
            </Button>
          </div>
        ) : currentQuestion ? (
          <div className="space-y-5">
            <div className="rounded-2xl border border-border/60 bg-muted/20 p-5">
              <div className="mb-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Вопрос {currentIndex + 1} из {sessionQuestions.length}
              </div>
              <ExamPrepContent value={currentQuestion.prompt} />
            </div>

            <div className="rounded-2xl border border-border/60 bg-background/90 p-5">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="font-medium text-foreground">Ответ</div>
                <Button type="button" variant="outline" onClick={() => setShowAnswer((current) => !current)}>
                  {showAnswer ? 'Скрыть' : hasExamPrepContent(currentQuestion.answer) ? 'Показать ответ' : 'Самопроверка'}
                </Button>
              </div>
              {showAnswer ? (
                <ExamPrepContent
                  value={currentQuestion.answer}
                  placeholder="Сформулируй ответ своими словами и сравни с лекциями или конспектом."
                />
              ) : (
                <div className="text-sm text-muted-foreground">
                  Попробуй ответить устно или письменно, затем открывай ответ и оценивай себя.
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="secondary" onClick={() => answerCurrent('repeat')}>
                Повторить
              </Button>
              <Button type="button" onClick={() => answerCurrent('known')}>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Знаю
              </Button>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
