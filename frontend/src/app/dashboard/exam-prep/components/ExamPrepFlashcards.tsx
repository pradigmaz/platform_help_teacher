'use client';

import { useMemo, useState } from 'react';
import { BookOpenText, RotateCcw, Shuffle } from 'lucide-react';
import Stack from '@/components/Stack';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ExamPrepQuestion } from '@/lib/api';
import { getExamPrepText, hasExamPrepContent, pickQuizQuestions } from '@/lib/utils/exam-prep';
import { ExamPrepContent } from './ExamPrepContent';

export function ExamPrepFlashcards({ questions }: { questions: ExamPrepQuestion[] }) {
  const [deck, setDeck] = useState<ExamPrepQuestion[]>(questions);
  const [showAnswer, setShowAnswer] = useState(false);
  const [stats, setStats] = useState({ known: 0, repeat: 0 });

  const currentQuestion = deck[0];
  const cards = useMemo(
    () =>
      deck.slice(0, 3).map((question, index) => (
        <div key={question.id} className="flex h-full w-full items-stretch">
          <Card className="flex h-full w-full flex-col border-border/60 bg-background/95 shadow-xl">
            <CardHeader className="space-y-2">
              <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                {index === 0 ? (showAnswer ? 'Ответ' : 'Вопрос') : `Карточка ${index + 1}`}
              </div>
              <CardTitle className="text-xl">
                {index === 0 ? getExamPrepText(question.prompt) : getExamPrepText(question.prompt)}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1">
              {index === 0 ? (
                showAnswer ? (
                  <ExamPrepContent
                    value={question.answer}
                    placeholder="Сформулируй ответ своими словами и сверяйся с лекцией."
                  />
                ) : (
                  <ExamPrepContent value={question.prompt} />
                )
              ) : (
                <div className="text-sm text-muted-foreground">
                  Следующая карточка: {getExamPrepText(question.prompt)}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )),
    [deck, showAnswer],
  );

  function rotateDeck(result?: 'known' | 'repeat') {
    if (!currentQuestion) {
      return;
    }
    if (result) {
      setStats((current) => ({ ...current, [result]: current[result] + 1 }));
    }
    setDeck((current) => (current.length > 1 ? [...current.slice(1), current[0]] : current));
    setShowAnswer(false);
  }

  function shuffleDeck() {
    setDeck((current) => pickQuizQuestions(current, current.length));
    setShowAnswer(false);
  }

  return (
    <Card className="border-border/60 bg-background/80 shadow-sm">
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <CardTitle className="flex items-center gap-2 text-xl">
            <BookOpenText className="h-5 w-5 text-primary" />
            Карточки
          </CardTitle>
          <div className="text-sm text-muted-foreground">
            Сначала попробуй ответить по памяти. Потом переворачивай карточку и отмечай, что уже знаешь.
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">Знаю: {stats.known}</Badge>
          <Badge variant="outline">Повторить: {stats.repeat}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="h-[420px] overflow-hidden rounded-3xl border border-border/60 bg-muted/20 p-4">
          <Stack key={`${currentQuestion?.id ?? 'empty'}-${showAnswer ? 'answer' : 'question'}`} cards={cards} />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" variant="outline" onClick={() => setShowAnswer((current) => !current)}>
            {showAnswer ? 'Показать вопрос' : hasExamPrepContent(currentQuestion?.answer) ? 'Показать ответ' : 'Самопроверка'}
          </Button>
          <Button type="button" variant="outline" onClick={shuffleDeck}>
            <Shuffle className="mr-2 h-4 w-4" />
            Перемешать
          </Button>
          <Button type="button" variant="outline" onClick={() => rotateDeck()}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Следующая
          </Button>
          <Button type="button" variant="secondary" onClick={() => rotateDeck('repeat')}>
            Повторить
          </Button>
          <Button type="button" onClick={() => rotateDeck('known')}>
            Знаю
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
