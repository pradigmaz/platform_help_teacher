'use client';

import { Calendar, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BlurFade } from '@/components/ui/blur-fade';
import { LabSubmission } from './types';

const STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  NEW: { color: 'bg-blue-500', icon: <Clock className="w-3 h-3" />, label: 'Новая' },
  IN_REVIEW: { color: 'bg-yellow-500', icon: <Clock className="w-3 h-3" />, label: 'На проверке' },
  REQ_CHANGES: { color: 'bg-orange-500', icon: <AlertCircle className="w-3 h-3" />, label: 'Доработка' },
  ACCEPTED: { color: 'bg-green-500', icon: <CheckCircle className="w-3 h-3" />, label: 'Принято' },
  REJECTED: { color: 'bg-red-500', icon: <XCircle className="w-3 h-3" />, label: 'Отклонено' },
};

interface Props {
  labs: LabSubmission[];
}

export function StudentLabsList({ labs }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Лабораторные работы
        </CardTitle>
      </CardHeader>
      <CardContent>
        {labs.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">Нет лабораторных работ</p>
        ) : (
          <div className="space-y-3">
            {labs.map((lab, index) => {
              const resolvedStatus = lab.normalized_status ?? lab.status;
              const statusConfig = resolvedStatus ? STATUS_CONFIG[resolvedStatus] : null;
              return (
                <BlurFade key={lab.lab_id} delay={0.65 + index * 0.05}>
                  <div
                    className={`flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-all duration-200 hover:shadow-md ${
                      lab.is_overdue ? 'border-orange-500 bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900/10 dark:to-red-900/10' : ''
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium truncate">{lab.lab_title}</span>
                        {lab.is_overdue && (
                          <Badge variant="destructive" className="text-xs animate-pulse">Долг</Badge>
                        )}
                      </div>
                      <div className="flex gap-4 text-sm text-muted-foreground mt-1">
                        {lab.deadline_5_lessons && (
                          <span>На 5: {lab.deadline_5_lessons === 1 ? 'След. пара' : `Через ${lab.deadline_5_lessons - 1} пар`}</span>
                        )}
                        {lab.submitted_at && (
                          <span>Сдано: {new Date(lab.submitted_at).toLocaleDateString('ru-RU')}</span>
                        )}
                      </div>
                      {lab.feedback && (
                        <div className="text-sm text-yellow-600 dark:text-yellow-400 mt-1">
                          💬 {lab.feedback}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      {lab.grade !== null ? (
                        <span className="font-bold text-green-600 dark:text-green-400">
                          {lab.grade}/{lab.max_grade}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—/{lab.max_grade}</span>
                      )}
                      {statusConfig ? (
                        <Badge className={`${statusConfig.color} text-white gap-1`}>
                          {statusConfig.icon}
                          {statusConfig.label}
                        </Badge>
                      ) : (
                        <Badge variant="outline">Не сдано</Badge>
                      )}
                    </div>
                  </div>
                </BlurFade>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
