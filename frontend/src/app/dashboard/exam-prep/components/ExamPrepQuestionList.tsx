'use client';

import { useState } from 'react';
import { Eye, EyeOff, MessageSquareQuote } from 'lucide-react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ExamPrepQuestion } from '@/lib/api';
import { getExamPrepText, hasExamPrepContent } from '@/lib/utils/exam-prep';
import { ExamPrepContent } from './ExamPrepContent';

export function ExamPrepQuestionList({ questions }: { questions: ExamPrepQuestion[] }) {
  const [revealedAnswers, setRevealedAnswers] = useState<Record<string, boolean>>({});

  return (
    <Card className="border-border/60 bg-background/80 shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <MessageSquareQuote className="h-5 w-5 text-primary" />
          Вопросы по списку
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible className="w-full">
          {questions.map((question, index) => {
            const hasAnswer = hasExamPrepContent(question.answer);
            const isRevealed = Boolean(revealedAnswers[question.id]);

            return (
              <AccordionItem key={question.id} value={question.id}>
                <AccordionTrigger>
                  <div className="pr-4 text-left">
                    <div className="text-xs text-muted-foreground">Вопрос {index + 1}</div>
                    <div className="line-clamp-2 font-medium text-foreground">{getExamPrepText(question.prompt)}</div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-4">
                  <ExamPrepContent value={question.prompt} />
                  <div className="rounded-xl border border-border/60 bg-muted/20 p-4">
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <div className="text-sm font-medium text-foreground">Ответ</div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setRevealedAnswers((current) => ({
                            ...current,
                            [question.id]: !current[question.id],
                          }))
                        }
                      >
                        {isRevealed ? <EyeOff className="mr-2 h-4 w-4" /> : <Eye className="mr-2 h-4 w-4" />}
                        {isRevealed ? 'Скрыть ответ' : hasAnswer ? 'Показать ответ' : 'Самопроверка'}
                      </Button>
                    </div>
                    {isRevealed ? (
                      <ExamPrepContent
                        value={question.answer}
                        placeholder="Сформулируй ответ своими словами и сравни с конспектом или лекцией."
                      />
                    ) : (
                      <div className="text-sm text-muted-foreground">
                        Попробуй сначала ответить по памяти, потом открывай ответ.
                      </div>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </Accordion>
      </CardContent>
    </Card>
  );
}
