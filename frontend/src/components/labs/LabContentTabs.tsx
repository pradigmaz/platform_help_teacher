'use client';

import { useState } from 'react';
import { Lab } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LectureViewer } from '@/components/lectures/LectureViewer';
import { SerializedEditorState } from 'lexical';
import { BookOpen, Code } from 'lucide-react';

interface LabContentTabsProps {
  lab: Lab;
}

export function LabContentTabs({ lab }: LabContentTabsProps) {
  const [activeSection, setActiveSection] = useState<'theory' | 'practice'>('theory');

  return (
    <>
      {/* Content tabs */}
      <div className="flex gap-2 border-b">
        <Button
          variant={activeSection === 'theory' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveSection('theory')}
          className="gap-1.5"
        >
          <BookOpen className="h-4 w-4" />
          Теория
        </Button>
        <Button
          variant={activeSection === 'practice' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setActiveSection('practice')}
          className="gap-1.5"
        >
          <Code className="h-4 w-4" />
          Практика
        </Button>
      </div>

      {/* Theory content */}
      {activeSection === 'theory' && lab.theory_content && (
        <Card>
          <CardContent className="py-6">
            <LectureViewer
              content={lab.theory_content as unknown as SerializedEditorState}
              title=""
            />
          </CardContent>
        </Card>
      )}

      {/* Practice content */}
      {activeSection === 'practice' && (
        <div className="space-y-4">
          {lab.practice_content && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base">Общее задание</CardTitle>
              </CardHeader>
              <CardContent className="py-3">
                <LectureViewer
                  content={lab.practice_content as unknown as SerializedEditorState}
                  title=""
                />
              </CardContent>
            </Card>
          )}

          {/* Variants */}
          {lab.variants && lab.variants.length > 0 && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-base">Варианты ({lab.variants.length})</CardTitle>
              </CardHeader>
              <CardContent className="py-3 space-y-3">
                {lab.variants.map((v: { number: number; description: string; test_data?: string }, i: number) => (
                  <div key={i} className="flex gap-3 p-3 rounded-lg border bg-muted/30">
                    <Badge variant="secondary" className="h-6 w-6 flex items-center justify-center shrink-0">
                      {v.number}
                    </Badge>
                    <div className="flex-1">
                      <p className="font-medium">{v.description || 'Без описания'}</p>
                      {v.test_data && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Тестовые данные: {v.test_data}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </>
  );
}
