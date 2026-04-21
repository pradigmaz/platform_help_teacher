'use client';

import { useEffect, useMemo, useState } from 'react';
import { BookOpenText, GraduationCap, Layers3 } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StudentAPI, type StudentExamPrepOffering, type StudentExamPrepResponse } from '@/lib/api';
import { ExamPrepFlashcards } from './components/ExamPrepFlashcards';
import { ExamPrepQuestionList } from './components/ExamPrepQuestionList';
import { ExamPrepQuiz } from './components/ExamPrepQuiz';

export default function ExamPrepPage() {
  const [offerings, setOfferings] = useState<StudentExamPrepOffering[]>([]);
  const [selectedOfferingId, setSelectedOfferingId] = useState<string>('');
  const [payload, setPayload] = useState<StudentExamPrepResponse | null>(null);
  const [loadingOfferings, setLoadingOfferings] = useState(true);
  const [loadingPayload, setLoadingPayload] = useState(false);
  const [offeringsLoadFailed, setOfferingsLoadFailed] = useState(false);
  const [payloadLoadFailed, setPayloadLoadFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const loadOfferings = async () => {
      setLoadingOfferings(true);
      setOfferingsLoadFailed(false);
      try {
        const nextOfferings = await StudentAPI.getExamPrepOfferings();
        if (!cancelled) {
          setOfferings(nextOfferings);
          setSelectedOfferingId((current) => current || nextOfferings[0]?.offering_id || '');
        }
      } catch {
        if (!cancelled) {
          setOfferingsLoadFailed(true);
          toast.error('Не удалось загрузить экзамены для подготовки');
        }
      } finally {
        if (!cancelled) {
          setLoadingOfferings(false);
        }
      }
    };

    void loadOfferings();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedOfferingId) {
      setPayload(null);
      setPayloadLoadFailed(false);
      return;
    }

    let cancelled = false;
    const loadPayload = async () => {
      setPayload(null);
      setPayloadLoadFailed(false);
      setLoadingPayload(true);
      try {
        const nextPayload = await StudentAPI.getExamPrep(selectedOfferingId);
        if (!cancelled) {
          setPayload(nextPayload);
        }
      } catch {
        if (!cancelled) {
          setPayload(null);
          setPayloadLoadFailed(true);
          toast.error('Не удалось загрузить вопросы для подготовки');
        }
      } finally {
        if (!cancelled) {
          setLoadingPayload(false);
        }
      }
    };

    void loadPayload();

    return () => {
      cancelled = true;
    };
  }, [selectedOfferingId]);

  const selectedOffering = useMemo(
    () => offerings.find((offering) => offering.offering_id === selectedOfferingId) ?? null,
    [offerings, selectedOfferingId],
  );

  if (loadingOfferings) {
    return <div className="mx-auto max-w-6xl p-6 text-sm text-muted-foreground">Загрузка экзаменационной подготовки…</div>;
  }

  if (!offerings.length) {
    return (
      <div className="mx-auto max-w-6xl p-6">
        <Card className="border-dashed border-border/60 bg-background/80">
          <CardContent className="flex flex-col items-center gap-4 py-14 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted/60">
              <GraduationCap className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              {offeringsLoadFailed ? (
                <>
                  <div className="text-xl font-semibold text-foreground">Не удалось загрузить экзамены</div>
                  <div className="max-w-xl text-sm text-muted-foreground">
                    Список экзаменов временно недоступен. Попробуй обновить страницу чуть позже.
                  </div>
                </>
              ) : (
                <>
                  <div className="text-xl font-semibold text-foreground">Подготовка пока недоступна</div>
                  <div className="max-w-xl text-sm text-muted-foreground">
                    Раздел появляется, когда для одного из предметов текущего семестра преподаватель выставляет форму контроля «Экзамен».
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="space-y-2">
        <h1 className="flex items-center gap-3 text-3xl font-bold tracking-tight">
          <BookOpenText className="h-8 w-8 text-primary" />
          Подготовка к экзамену
        </h1>
        <p className="text-muted-foreground">
          Один банк вопросов, три режима подготовки: обычный список, карточки и короткий self-check квиз.
        </p>
      </div>

      {offerings.length > 1 ? (
        <Card className="border-border/60 bg-background/80 shadow-sm">
          <CardContent className="space-y-4 p-5">
            <div className="space-y-1">
              <div className="text-sm font-medium text-foreground">Выбор экзамена</div>
              <div className="text-sm text-muted-foreground">Если в семестре несколько экзаменов, выбери нужный предмет.</div>
            </div>
            <Select value={selectedOfferingId} onValueChange={setSelectedOfferingId}>
              <SelectTrigger className="max-w-md">
                <SelectValue placeholder="Выберите экзамен" />
              </SelectTrigger>
              <SelectContent>
                {offerings.map((offering) => (
                  <SelectItem key={offering.offering_id} value={offering.offering_id}>
                    {offering.subject_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-border/60 bg-background/80 shadow-sm">
          <CardContent className="p-5">
            <div className="text-sm text-muted-foreground">Предмет</div>
            <div className="mt-2 text-xl font-semibold text-foreground">{selectedOffering?.subject_name}</div>
          </CardContent>
        </Card>
        <Card className="border-border/60 bg-background/80 shadow-sm">
          <CardContent className="p-5">
            <div className="text-sm text-muted-foreground">Семестр</div>
            <div className="mt-2 text-xl font-semibold text-foreground">{selectedOffering?.semester}</div>
          </CardContent>
        </Card>
        <Card className="border-border/60 bg-background/80 shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Layers3 className="h-4 w-4" />
              Вопросов
            </div>
            <div className="mt-2 flex items-center gap-2 text-xl font-semibold text-foreground">
              {payload?.questions_count ?? selectedOffering?.questions_count ?? 0}
              <Badge variant="outline">Экзамен</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {loadingPayload ? (
        <Card className="border-border/60 bg-background/80 shadow-sm">
          <CardContent className="py-12 text-center text-sm text-muted-foreground">Загрузка вопросов…</CardContent>
        </Card>
      ) : payload && payload.questions.length > 0 ? (
        <Tabs defaultValue="questions" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="questions">Вопросы</TabsTrigger>
            <TabsTrigger value="cards">Карточки</TabsTrigger>
            <TabsTrigger value="quiz">Квиз</TabsTrigger>
          </TabsList>
          <TabsContent value="questions">
            <ExamPrepQuestionList
              key={selectedOfferingId || payload.offering_id}
              questions={payload.questions}
            />
          </TabsContent>
          <TabsContent value="cards">
            <ExamPrepFlashcards
              key={selectedOfferingId || payload.offering_id}
              questions={payload.questions}
            />
          </TabsContent>
          <TabsContent value="quiz">
            <ExamPrepQuiz questions={payload.questions} />
          </TabsContent>
        </Tabs>
      ) : payloadLoadFailed ? (
        <Card className="border-dashed border-border/60 bg-background/80 shadow-sm">
          <CardContent className="py-14 text-center">
            <div className="text-xl font-semibold text-foreground">Не удалось загрузить вопросы</div>
            <div className="mt-2 text-sm text-muted-foreground">
              Банк вопросов временно недоступен. Попробуй открыть экзамен ещё раз чуть позже.
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="border-dashed border-border/60 bg-background/80 shadow-sm">
          <CardContent className="py-14 text-center">
            <div className="text-xl font-semibold text-foreground">Вопросы ещё не добавлены</div>
            <div className="mt-2 text-sm text-muted-foreground">
              Для этого экзамена преподаватель пока не заполнил банк вопросов.
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
