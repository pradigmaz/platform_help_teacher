'use client';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Users, FlaskConical, Clock, RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import type { LabQueue, SubmissionDetail } from '@/lib/api/types/lab-queue';

interface QueueDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  queue: LabQueue[];
  loading: boolean;
  onRefresh: () => void;
  selectedSubmission: SubmissionDetail | null;
  onSelectSubmission: (id: string) => void;
  onAccept: () => void;
  onReject: () => void;
}

export function QueueDialog({
  open,
  onOpenChange,
  queue,
  loading,
  onRefresh,
  selectedSubmission,
  onSelectSubmission,
  onAccept,
  onReject,
}: QueueDialogProps) {
  const totalInQueue = queue.reduce((sum, lab) => sum + lab.queue.length, 0);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <Users className="w-5 h-5" />
            Очередь на сдачу
            {totalInQueue > 0 && (
              <Badge variant="secondary">{totalInQueue}</Badge>
            )}
          </DialogTitle>
          <div className="absolute right-10 top-4">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={onRefresh}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
          <DialogDescription>
            Студенты, готовые сдать лабораторные работы
          </DialogDescription>
        </DialogHeader>
        
        <ScrollArea className="max-h-[50vh]">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : queue.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="w-12 h-12 mx-auto mb-3 opacity-20" />
              <p>Очередь пуста</p>
            </div>
          ) : (
            <div className="space-y-4">
              {queue.map((labQueue) => (
                <Card key={labQueue.lab_id}>
                  <CardHeader className="py-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <FlaskConical className="w-4 h-4" />
                      Лаба #{labQueue.lab_number}: {labQueue.lab_title}
                      <Badge variant="outline" className="ml-auto">{labQueue.queue.length}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="py-2">
                    <div className="space-y-2">
                      {labQueue.queue.map((item) => (
                        <div
                          key={item.submission_id}
                          className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                            selectedSubmission?.submission_id === item.submission_id
                              ? 'bg-primary/10 border-primary'
                              : 'hover:bg-muted/50'
                          }`}
                          onClick={() => onSelectSubmission(item.submission_id)}
                        >
                          <div>
                            <div className="font-medium">{item.student_name}</div>
                            <div className="text-sm text-muted-foreground flex items-center gap-2">
                              <span>{item.group_name}</span>
                              {item.variant_number && (
                                <Badge variant="secondary" className="text-xs">
                                  Вариант {item.variant_number}
                                </Badge>
                              )}
                            </div>
                          </div>
                          <div className="text-sm text-muted-foreground flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(item.ready_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </ScrollArea>

        {selectedSubmission && (
          <div className="border-t pt-4 mt-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="font-medium">{selectedSubmission.student_name}</div>
                <div className="text-sm text-muted-foreground">
                  {selectedSubmission.group_name} • Лаба #{selectedSubmission.lab_number}
                  {selectedSubmission.variant_number && ` • Вариант ${selectedSubmission.variant_number}`}
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={onReject}>
                  <XCircle className="w-4 h-4 mr-1" />
                  Отклонить
                </Button>
                <Button size="sm" onClick={onAccept}>
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Принять
                </Button>
              </div>
            </div>
            
            {selectedSubmission.questions && selectedSubmission.questions.length > 0 && (
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-sm font-medium mb-2">Контрольные вопросы:</div>
                <ol className="text-sm space-y-1 list-decimal list-inside">
                  {selectedSubmission.questions.map((q, i) => (
                    <li key={i}>{q}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
