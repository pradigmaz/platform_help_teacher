'use client';

import { useState } from 'react';
import { AlertTriangle, Check, X, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Card,
  CardContent,
} from '@/components/ui/card';
import { toast } from '@/components/ui/sonner';
import api from '@/lib/api';

export interface ScheduleConflict {
  id: string;
  lesson_id: string;
  conflict_type: 'changed' | 'deleted';
  old_data: {
    topic?: string;
    lesson_type?: string;
    room?: string;
    date?: string;
    lesson_number?: number;
  };
  new_data: {
    topic?: string;
    lesson_type?: string;
    room?: string;
    date?: string;
    lesson_number?: number;
  } | null;
  created_at: string;
}

interface ConflictResolverProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  conflicts: ScheduleConflict[];
  onRefresh: () => void;
}

export function ConflictResolver({ 
  open, 
  onOpenChange, 
  conflicts,
  onRefresh
}: ConflictResolverProps) {
  const [resolving, setResolving] = useState<string | null>(null);

  const handleResolve = async (conflictId: string, action: 'accept' | 'reject') => {
    setResolving(conflictId);
    try {
      await api.post(`/admin/schedule/conflicts/${conflictId}/resolve`, { action });
      toast.success(action === 'accept' ? 'Изменение принято' : 'Изменение отклонено');
      onRefresh();
    } catch {
      toast.error('Ошибка');
    } finally {
      setResolving(null);
    }
  };

  const handleResolveAll = async (action: 'accept' | 'reject') => {
    setResolving('all');
    try {
      await api.post('/admin/schedule/conflicts/resolve-all', { action });
      toast.success(action === 'accept' ? 'Все изменения приняты' : 'Все изменения отклонены');
      onRefresh();
      onOpenChange(false);
    } catch {
      toast.error('Ошибка');
    } finally {
      setResolving(null);
    }
  };

  const changedConflicts = conflicts.filter(c => c.conflict_type === 'changed');
  const deletedConflicts = conflicts.filter(c => c.conflict_type === 'deleted');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            Конфликты расписания ({conflicts.length})
          </DialogTitle>
          <DialogDescription>
            Обнаружены изменения в расписании. Выберите действие для каждого конфликта.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          {/* Changed lessons */}
          {changedConflicts.length > 0 && (
            <div>
              <h3 className="font-medium mb-2 flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-blue-500" />
                Изменённые занятия ({changedConflicts.length})
              </h3>
              <div className="space-y-2">
                {changedConflicts.map(conflict => (
                  <Card key={conflict.id} className="border-blue-200">
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="text-muted-foreground text-xs mb-1">Было:</div>
                            <div>{conflict.old_data.topic || 'Без темы'}</div>
                            <div className="text-muted-foreground">
                              {conflict.old_data.lesson_type} • {conflict.old_data.room}
                            </div>
                          </div>
                          <div>
                            <div className="text-muted-foreground text-xs mb-1">Стало:</div>
                            <div>{conflict.new_data?.topic || 'Без темы'}</div>
                            <div className="text-muted-foreground">
                              {conflict.new_data?.lesson_type} • {conflict.new_data?.room}
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleResolve(conflict.id, 'reject')}
                            disabled={resolving === conflict.id}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleResolve(conflict.id, 'accept')}
                            disabled={resolving === conflict.id}
                          >
                            <Check className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Deleted lessons */}
          {deletedConflicts.length > 0 && (
            <div>
              <h3 className="font-medium mb-2 flex items-center gap-2">
                <X className="w-4 h-4 text-red-500" />
                Отменённые занятия ({deletedConflicts.length})
              </h3>
              <div className="space-y-2">
                {deletedConflicts.map(conflict => (
                  <Card key={conflict.id} className="border-red-200">
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between gap-4">
                        <div className="text-sm">
                          <div>{conflict.old_data.topic || 'Без темы'}</div>
                          <div className="text-muted-foreground">
                            {conflict.old_data.date} • {conflict.old_data.lesson_number} пара
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleResolve(conflict.id, 'reject')}
                            disabled={resolving === conflict.id}
                            title="Оставить занятие"
                          >
                            Оставить
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleResolve(conflict.id, 'accept')}
                            disabled={resolving === conflict.id}
                            title="Отменить занятие"
                          >
                            Отменить
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button 
            variant="outline" 
            onClick={() => handleResolveAll('reject')}
            disabled={resolving === 'all'}
          >
            Отклонить все
          </Button>
          <Button 
            onClick={() => handleResolveAll('accept')}
            disabled={resolving === 'all'}
          >
            Принять все
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
