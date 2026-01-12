'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { IconTarget, IconBook, IconCode, IconQuestionMark, IconFlask } from '@tabler/icons-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import api from '@/lib/api';
import { LectureViewer } from '@/components/lectures';
import { getQuestionText } from '@/lib/utils/question-utils';

import { SerializedEditorState } from 'lexical';

interface PublicLab {
  id: string;
  number: number;
  title: string;
  topic?: string;
  goal?: string;
  formatting_guide?: string;
  theory_content?: SerializedEditorState;
  practice_content?: SerializedEditorState;
  variants?: { number: number; description: string; test_data?: string }[];
  questions?: (string | { text?: string; content?: SerializedEditorState })[];
  max_grade: number;
}

export default function PublicLabPage() {
  const params = useParams();
  const code = params.code as string;
  
  const [lab, setLab] = useState<PublicLab | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadLab = async () => {
      try {
        const { data } = await api.get<PublicLab>(`/labs/view/${code}`);
        setLab(data);
      } catch {
        setError('Лабораторная не найдена');
      } finally {
        setLoading(false);
      }
    };
    loadLab();
  }, [code]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <Skeleton className="h-12 w-3/4" />
        <Skeleton className="h-[400px]" />
      </div>
    );
  }

  if (error || !lab) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card>
          <CardContent className="py-16 text-center">
            <IconFlask className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h2 className="text-xl font-semibold mb-2">Лабораторная не найдена</h2>
            <p className="text-muted-foreground">Проверьте правильность ссылки</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Badge variant="outline">Лабораторная №{lab.number}</Badge>
        </div>
        <h1 className="text-3xl font-bold">{lab.title}</h1>
        {lab.topic && <p className="text-lg text-muted-foreground">{lab.topic}</p>}
      </div>

      <Tabs defaultValue="header">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="header" className="gap-2"><IconTarget className="h-4 w-4" />Шапка</TabsTrigger>
          <TabsTrigger value="theory" className="gap-2"><IconBook className="h-4 w-4" />Теория</TabsTrigger>
          <TabsTrigger value="practice" className="gap-2"><IconCode className="h-4 w-4" />Практика</TabsTrigger>
          <TabsTrigger value="questions" className="gap-2"><IconQuestionMark className="h-4 w-4" />Вопросы</TabsTrigger>
        </TabsList>

        <TabsContent value="header" className="space-y-4">
          {lab.goal && (
            <Card>
              <CardHeader><CardTitle>Цель работы</CardTitle></CardHeader>
              <CardContent><p className="whitespace-pre-wrap">{lab.goal}</p></CardContent>
            </Card>
          )}
          {lab.formatting_guide && (
            <Card>
              <CardHeader><CardTitle>Что записать в тетрадь</CardTitle></CardHeader>
              <CardContent><p className="whitespace-pre-wrap">{lab.formatting_guide}</p></CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="theory">
          <Card>
            <CardContent className="pt-6">
              {lab.theory_content ? (
                <LectureViewer content={lab.theory_content} />
              ) : (
                <p className="text-muted-foreground text-center py-8">Теоретическая часть не заполнена</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="practice" className="space-y-4">
          {lab.practice_content && (
            <Card>
              <CardHeader><CardTitle>Задание</CardTitle></CardHeader>
              <CardContent>
                <LectureViewer content={lab.practice_content} />
              </CardContent>
            </Card>
          )}
          {lab.variants && lab.variants.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Варианты</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {lab.variants.map((v) => (
                    <div key={v.number} className="p-3 border rounded-lg">
                      <div className="font-medium mb-1">Вариант {v.number}</div>
                      <p className="text-sm whitespace-pre-wrap">{v.description}</p>
                      {v.test_data && (
                        <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">{v.test_data}</pre>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="questions">
          <Card>
            <CardHeader><CardTitle>Контрольные вопросы</CardTitle></CardHeader>
            <CardContent>
              {lab.questions && lab.questions.length > 0 ? (
                <ol className="list-decimal list-inside space-y-2">
                  {lab.questions.map((q, i) => (
                    <li key={i} className="text-sm">{getQuestionText(q)}</li>
                  ))}
                </ol>
              ) : (
                <p className="text-muted-foreground text-center py-8">Контрольные вопросы не заполнены</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
