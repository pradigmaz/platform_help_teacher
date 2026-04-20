'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { BookOpenCheck, GraduationCap, NotebookTabs, SquarePen } from 'lucide-react';
import { BlurFade } from '@/components/ui/blur-fade';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ExamPrepEditorSheet } from '@/app/admin/subjects/components/ExamPrepEditorSheet';
import { useAdminExamOfferings } from '@/components/admin/useAdminExamOfferings';
import type { GroupSubjectOffering } from '@/lib/api';

function formatQuestionCount(count: number) {
  if (count === 1) {
    return '1 вопрос';
  }
  if (count > 1 && count < 5) {
    return `${count} вопроса`;
  }
  return `${count} вопросов`;
}

export default function AdminExamsPage() {
  const { examOfferings, isLoading, error, refetch } = useAdminExamOfferings();
  const [examPrepOffering, setExamPrepOffering] = useState<GroupSubjectOffering | null>(null);

  const filledBanksCount = useMemo(
    () => examOfferings.filter((offering) => offering.exam_prep_questions_count > 0).length,
    [examOfferings],
  );

  function handleExamPrepSaved(questionsCount: number) {
    setExamPrepOffering((current) =>
      current
        ? {
            ...current,
            exam_prep_questions_count: questionsCount,
          }
        : current,
    );
    void refetch({ force: true });
  }

  return (
    <div className="space-y-6">
      <BlurFade delay={0.1}>
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold tracking-tight">
            <BookOpenCheck className="h-8 w-8 text-primary" />
            Экзамены
          </h1>
          <p className="mt-1 text-muted-foreground">
            Здесь ведётся банк вопросов к экзамену. Сам факт экзамена задаётся отдельно в разделе «Предметы групп».
          </p>
        </div>
      </BlurFade>

      <BlurFade delay={0.15}>
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="border-border/60 bg-background/80 shadow-none">
            <CardHeader className="pb-3">
              <CardDescription>Экзаменационных связок</CardDescription>
              <CardTitle className="text-3xl">{examOfferings.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/60 bg-background/80 shadow-none">
            <CardHeader className="pb-3">
              <CardDescription>Заполненных банков</CardDescription>
              <CardTitle className="text-3xl">{filledBanksCount}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-border/60 bg-background/80 shadow-none">
            <CardHeader className="pb-3">
              <CardDescription>Пустых экзаменов</CardDescription>
              <CardTitle className="text-3xl">{Math.max(examOfferings.length - filledBanksCount, 0)}</CardTitle>
            </CardHeader>
          </Card>
        </div>
      </BlurFade>

      <BlurFade delay={0.2}>
        {isLoading ? (
          <div className="rounded-xl border border-border/60 bg-background/80 p-10 text-center text-sm text-muted-foreground">
            Загружаю экзамены…
          </div>
        ) : !examOfferings.length ? (
          <Card className="border-dashed border-border/60 bg-background/80 shadow-none">
            <CardHeader>
              <CardTitle>Экзаменов пока нет</CardTitle>
              <CardDescription>
                Как только хотя бы у одной связки появится форма контроля «Экзамен», этот раздел станет рабочим.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="text-sm text-muted-foreground">
                Если нужно, сначала выставьте экзамен в разделе «Предметы групп».
              </div>
              <Button asChild>
                <Link href="/admin/subjects">Открыть предметы групп</Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 xl:grid-cols-2">
            {examOfferings.map((offering) => (
              <Card key={offering.id} className="border-border/60 bg-background/80 shadow-none">
                <CardHeader className="gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">Экзамен</Badge>
                    <Badge variant="outline">{offering.semester}</Badge>
                    <Badge variant="outline">{formatQuestionCount(offering.exam_prep_questions_count)}</Badge>
                  </div>
                  <div className="space-y-2">
                    <CardTitle className="text-xl">{offering.subject_name}</CardTitle>
                    <CardDescription className="flex flex-wrap gap-4 text-sm">
                      <span className="inline-flex items-center gap-2">
                        <GraduationCap className="h-4 w-4" />
                        {offering.group_name}
                      </span>
                      <span className="inline-flex items-center gap-2">
                        <NotebookTabs className="h-4 w-4" />
                        {offering.semester}
                      </span>
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="text-sm text-muted-foreground">
                    {offering.exam_prep_questions_count > 0
                      ? 'Банк вопросов уже заполнен и доступен студентам в режиме подготовки.'
                      : 'Вопросы пока не добавлены. Студенты увидят пустое состояние до заполнения банка.'}
                  </div>
                  <Button type="button" onClick={() => setExamPrepOffering(offering)}>
                    <SquarePen className="mr-2 h-4 w-4" />
                    Открыть вопросы
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </BlurFade>

      {error && !examOfferings.length ? (
        <div className="rounded-xl border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          Не удалось обновить список экзаменов. Повторите позже или откройте страницу ещё раз.
        </div>
      ) : null}

      <ExamPrepEditorSheet
        open={Boolean(examPrepOffering)}
        onOpenChange={(open) => !open && setExamPrepOffering(null)}
        offering={examPrepOffering}
        onSaved={handleExamPrepSaved}
      />
    </div>
  );
}
