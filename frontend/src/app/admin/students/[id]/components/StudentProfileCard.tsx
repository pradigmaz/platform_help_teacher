'use client';

import { User, Users, Award, Trophy, Unlink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { BorderBeam } from '@/components/ui/border-beam';
import { Sparkles } from '@/components/ui/sparkles';
import { TransferStudentDialog } from '@/components/admin/TransferStudentDialog';
import { StudentProfile } from './types';

interface Props {
  student: StudentProfile;
  onResetTelegram: () => void;
  resettingTelegram: boolean;
  onTransferSuccess: () => void;
}

export function StudentProfileCard({ student, onResetTelegram, resettingTelegram, onTransferSuccess }: Props) {
  const { stats } = student;

  return (
    <Card className="relative overflow-hidden bg-gradient-to-br from-background via-background to-primary/5">
      <BorderBeam size={250} duration={12} delay={9} />
      <CardContent className="pt-6">
        <div className="flex items-start gap-6">
          <div className="relative">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary via-purple-500 to-pink-500 p-[3px]">
              <div className="w-full h-full rounded-full bg-background flex items-center justify-center">
                <User className="w-10 h-10 text-primary" />
              </div>
            </div>
            {stats.group_rank === 1 && (
              <div className="absolute -top-1 -right-1">
                <Sparkles color="#FFD700">
                  <Trophy className="w-6 h-6 text-yellow-500" />
                </Sparkles>
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold truncate">{student.full_name}</h2>
            {student.username && (
              <p className="text-muted-foreground">@{student.username}</p>
            )}
            <div className="flex flex-wrap gap-2 mt-3">
              {student.group_name && (
                <Badge variant="secondary" className="gap-1 px-3 py-1">
                  <Users className="w-3 h-3" /> {student.group_name}
                </Badge>
              )}
              <Badge 
                variant={student.is_active ? 'default' : 'destructive'}
                className={student.is_active ? 'bg-gradient-to-r from-green-500 to-emerald-500 dark:from-green-600 dark:to-emerald-600 text-white' : ''}
              >
                {student.is_active ? '● Активен' : '○ Неактивен'}
              </Badge>
              {stats.group_rank && stats.group_total && (
                <Badge variant="outline" className="gap-1 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border-yellow-500/30">
                  <Award className="w-3 h-3 text-yellow-500" />
                  <span className="font-bold">{stats.group_rank}</span> из {stats.group_total}
                </Badge>
              )}
            </div>
            
            <div className="mt-4 pt-4 border-t">
              <div className="flex gap-2">
                <TransferStudentDialog
                  studentId={student.id}
                  studentName={student.full_name}
                  currentGroupId={student.group_id || undefined}
                  currentGroupName={student.group_name || undefined}
                  onSuccess={onTransferSuccess}
                />
                {student.telegram_id && (
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline" size="sm" className="text-orange-600 border-orange-300 hover:bg-orange-50 dark:text-orange-400 dark:border-orange-700 dark:hover:bg-orange-900/20">
                        <Unlink className="w-4 h-4 mr-2" />
                        Отвязать Telegram
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Отвязать Telegram?</AlertDialogTitle>
                        <AlertDialogDescription>
                          Студент <strong>{student.full_name}</strong> потеряет доступ к системе через текущий Telegram-аккаунт. 
                          Ему нужно будет заново ввести инвайт-код в боте.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Отмена</AlertDialogCancel>
                        <AlertDialogAction 
                          onClick={onResetTelegram}
                          disabled={resettingTelegram}
                          className="bg-orange-600 hover:bg-orange-700"
                        >
                          {resettingTelegram ? 'Отвязываю...' : 'Да, отвязать'}
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
