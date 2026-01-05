'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sparkles, Trash2, Plus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { ActivitiesAPI, ActivityResponse } from '@/lib/api';
import { AddActivityDialog } from './AddActivityDialog';
import { BlurFade } from '@/components/ui/blur-fade';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface StudentActivitiesListProps {
  studentId: string;
  studentName: string;
}

export function StudentActivitiesList({ studentId, studentName }: StudentActivitiesListProps) {
  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const loadActivities = async () => {
    try {
      const data = await ActivitiesAPI.getByStudent(studentId);
      setActivities(data);
    } catch (error) {
      toast.error('Не удалось загрузить активность');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActivities();
  }, [studentId]);

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await ActivitiesAPI.delete(deleteId);
      toast.success('Активность удалена');
      loadActivities();
    } catch (error) {
      toast.error('Ошибка при удалении');
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Sparkles className="w-5 h-5 text-purple-500" />
          История активности
        </CardTitle>
        <Button size="sm" variant="outline" onClick={() => setAddDialogOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Добавить
        </Button>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : activities.length === 0 ? (
          <p className="text-center text-muted-foreground py-8 text-sm">
            Нет записей об активности
          </p>
        ) : (
          <div className="space-y-3">
            {activities.map((activity, index) => (
              <BlurFade key={activity.id} delay={0.1 + index * 0.05}>
                <div className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex-1 min-w-0 mr-4">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge 
                        variant={activity.points > 0 ? "default" : "destructive"}
                        className={activity.points > 0 ? "bg-green-500 hover:bg-green-600" : ""}
                      >
                        {activity.points > 0 ? '+' : ''}{activity.points}
                      </Badge>
                      <span className="text-xs text-muted-foreground bg-secondary px-2 py-0.5 rounded">
                        {activity.attestation_type === 'first' ? '1-я аттестация' : '2-я аттестация'}
                      </span>
                    </div>
                    <p className="text-sm font-medium leading-tight">
                      {activity.description}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(activity.created_at).toLocaleDateString('ru-RU', {
                        day: 'numeric',
                        month: 'long',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive shrink-0"
                    onClick={() => setDeleteId(activity.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </BlurFade>
            ))}
          </div>
        )}
      </CardContent>

      <AddActivityDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        targetId={studentId}
        targetName={studentName}
        mode="student"
        onSuccess={loadActivities}
      />

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить активность?</AlertDialogTitle>
            <AlertDialogDescription>
              Это действие отменит начисление баллов.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}

