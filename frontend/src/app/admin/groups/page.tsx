'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Plus, Users, Trash2 } from 'lucide-react';
import { GroupsAPI, GroupResponse } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/sonner';
import { Skeleton } from '@/components/ui/skeleton';
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
import { BentoCard, BentoGrid } from '@/components/ui/bento-grid';
import { DotPattern } from '@/components/ui/dot-pattern';

export default function AdminGroupsPage() {
  const [groups, setGroups] = useState<GroupResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    try {
      const data = await GroupsAPI.list();
      setGroups(data);
    } catch (e) {
      toast.error('Ошибка загрузки списка групп');
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await GroupsAPI.delete(deleteId);
      toast.success('Группа удалена');
      loadGroups();
    } catch (e) {
      toast.error('Ошибка при удалении');
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div className="relative min-h-screen p-8 space-y-8 max-w-7xl mx-auto overflow-hidden">
      <DotPattern
        className="[mask-image:radial-gradient(800px_circle_at_center,white,transparent)] opacity-40"
      />
      
      <div className="relative flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Учебные группы</h1>
          <p className="text-muted-foreground mt-2">
            Управление потоками и списками студентов.
          </p>
        </div>
        <Link href="/admin/groups/new">
          <Button size="lg" className="gap-2">
            <Plus className="w-4 h-4" /> Создать группу
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="flex flex-col p-6 bg-card border rounded-xl space-y-4">
              <div className="flex justify-between items-start">
                <Skeleton className="w-12 h-12 rounded-lg" />
                <Skeleton className="w-8 h-8 rounded-md" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </div>
              <div className="mt-auto pt-4 border-t flex justify-between items-center">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-6 w-10 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      ) : groups.length === 0 ? (
        <div className="text-center py-20 border-2 border-dashed rounded-xl">
          <Users className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium">Групп пока нет</h3>
          <p className="text-muted-foreground mb-4">Создайте первую группу, чтобы начать.</p>
          <Link href="/admin/groups/new">
            <Button variant="outline">Создать группу</Button>
          </Link>
        </div>
      ) : (
        <BentoGrid className="relative">
          {groups.map((group) => (
            <BentoCard
              key={group.id}
              name={group.name}
              className="md:col-span-1"
              background={<div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent" />}
              Icon={Users}
              description={`Код: ${group.code} • Студентов: ${group.students_count || 0}`}
              href={`/admin/groups/${group.id}`}
              cta="Управление группой"
            >
              <div className="absolute top-4 right-4 z-20">
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-destructive h-8 w-8"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setDeleteId(group.id);
                  }}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </BentoCard>
          ))}
        </BentoGrid>
      )}

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Вы уверены?</AlertDialogTitle>
            <AlertDialogDescription>
              Это действие нельзя отменить. Группа будет удалена, а студенты отвязаны.
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
    </div>
  );
}
