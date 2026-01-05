'use client';

import { AttestationResult, AttestationType } from '@/lib/api';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { 
  FlaskConical, 
  CalendarCheck, 
  Sparkles, 
  AlertTriangle,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface StudentDetailSheetProps {
  student: AttestationResult | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  attestationType: AttestationType;
}

export function StudentDetailSheet({ 
  student, 
  open, 
  onOpenChange, 
  attestationType 
}: StudentDetailSheetProps) {
  if (!student) return null;

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .slice(0, 2)
      .toUpperCase();
  };

  const isBorderline = !student.is_passing && 
    student.total_score >= student.min_passing_points - 5;

  const pointsToPass = student.min_passing_points - student.total_score;

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'отл': return 'bg-green-500 text-white';
      case 'хор': return 'bg-blue-500 text-white';
      case 'уд': return 'bg-yellow-500 text-white';
      case 'неуд': return 'bg-red-500 text-white';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const breakdown = student.components_breakdown;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md overflow-y-auto">
        <SheetHeader>
          <div className="flex items-center gap-4">
            <Avatar className="h-14 w-14">
              <AvatarFallback className="text-xl bg-primary/10 text-primary">
                {getInitials(student.student_name)}
              </AvatarFallback>
            </Avatar>
            <div>
              <SheetTitle className="text-left">{student.student_name}</SheetTitle>
              <SheetDescription className="text-left">
                {student.group_code && `${student.group_code} • `}
                {attestationType === 'first' ? '1-я' : '2-я'} аттестация
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Total Score Card */}
          <Card className={cn(
            "border-2",
            student.is_passing ? "border-green-500/30" : "border-red-500/30"
          )}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {student.is_passing ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                  <span className="font-medium">
                    {student.is_passing ? 'Зачёт' : 'Незачёт'}
                  </span>
                </div>
                <Badge className={getGradeColor(student.grade)}>
                  {student.grade}
                </Badge>
              </div>
              
              <div className="text-center mb-3">
                <span className="text-4xl font-bold">{student.total_score.toFixed(1)}</span>
                <span className="text-xl text-muted-foreground">/{student.max_points}</span>
              </div>
              
              <Progress 
                value={(student.total_score / student.max_points) * 100}
                className={cn(
                  "h-2",
                  student.is_passing ? "[&>div]:bg-green-500" : "[&>div]:bg-red-500"
                )}
              />
              
              <p className="text-xs text-center text-muted-foreground mt-2">
                Порог зачёта: {student.min_passing_points} баллов
              </p>
            </CardContent>
          </Card>

          <Separator />

          {/* Score Breakdown */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              Разбивка баллов
            </h3>

            {/* Labs */}
            <BreakdownCard
              icon={<FlaskConical className="h-4 w-4" />}
              title="Лабораторные"
              score={student.lab_score}
              maxScore={breakdown?.labs_weighted_score ? student.lab_score : 24}
              color="purple"
              details={breakdown ? (
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>Сдано: {breakdown.labs_count} из {breakdown.labs_required}</p>
                  {breakdown.labs_bonus > 0 && (
                    <p className="text-green-600">+{breakdown.labs_bonus.toFixed(1)} бонус</p>
                  )}
                </div>
              ) : null}
            />

            {/* Attendance */}
            <BreakdownCard
              icon={<CalendarCheck className="h-4 w-4" />}
              title="Посещаемость"
              score={student.attendance_score}
              maxScore={breakdown?.attendance_weighted_score ? student.attendance_score : 8}
              color="blue"
              details={breakdown ? (
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>Занятий: {breakdown.attendance_total_classes}</p>
                  <p>
                    ✓ {breakdown.attendance_present} | 
                    ⏰ {breakdown.attendance_late} | 
                    ✗ {breakdown.attendance_absent}
                  </p>
                </div>
              ) : null}
            />

            {/* Activity */}
            <BreakdownCard
              icon={<Sparkles className="h-4 w-4" />}
              title="Активность"
              score={student.activity_score}
              maxScore={8}
              color="amber"
              details={breakdown ? (
                <div className="text-xs text-muted-foreground">
                  <p>Начислено баллов: {breakdown.activity_raw_score}</p>
                </div>
              ) : null}
            />
          </div>

          {/* Borderline Warning */}
          {isBorderline && (
            <>
              <Separator />
              <Card className="border-yellow-500/30 bg-yellow-500/5">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="h-8 w-8 rounded-lg bg-yellow-500/20 flex items-center justify-center shrink-0">
                      <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    </div>
                    <div>
                      <p className="font-medium text-yellow-600">Пограничный результат</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        До зачёта не хватает <span className="font-semibold">{pointsToPass.toFixed(1)} баллов</span>.
                        Рекомендуется дополнительная активность или пересдача лабораторных.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {/* Not passing recommendations */}
          {!student.is_passing && !isBorderline && (
            <>
              <Separator />
              <Card className="border-red-500/30 bg-red-500/5">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="h-8 w-8 rounded-lg bg-red-500/20 flex items-center justify-center shrink-0">
                      <XCircle className="h-4 w-4 text-red-600" />
                    </div>
                    <div>
                      <p className="font-medium text-red-600">Требуется улучшение</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Для получения зачёта необходимо набрать ещё <span className="font-semibold">{pointsToPass.toFixed(1)} баллов</span>.
                      </p>
                      <ul className="text-sm text-muted-foreground mt-2 space-y-1 list-disc list-inside">
                        {breakdown && breakdown.labs_count < breakdown.labs_required && (
                          <li>Сдать недостающие лабораторные работы</li>
                        )}
                        <li>Получить баллы за активность</li>
                        <li>Улучшить посещаемость</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

interface BreakdownCardProps {
  icon: React.ReactNode;
  title: string;
  score: number;
  maxScore: number;
  color: 'purple' | 'blue' | 'amber';
  details?: React.ReactNode;
}

function BreakdownCard({ icon, title, score, maxScore, color, details }: BreakdownCardProps) {
  const colorClasses = {
    purple: 'bg-purple-500/10 text-purple-600',
    blue: 'bg-blue-500/10 text-blue-600',
    amber: 'bg-amber-500/10 text-amber-600',
  };

  const progressColors = {
    purple: '[&>div]:bg-purple-500',
    blue: '[&>div]:bg-blue-500',
    amber: '[&>div]:bg-amber-500',
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={cn("p-2 rounded-lg", colorClasses[color])}>
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium text-sm">{title}</span>
              <span className="font-semibold">
                {score.toFixed(1)}
                <span className="text-muted-foreground font-normal">/{maxScore}</span>
              </span>
            </div>
            <Progress 
              value={maxScore > 0 ? (score / maxScore) * 100 : 0}
              className={cn("h-1.5", progressColors[color])}
            />
            {details && <div className="mt-2">{details}</div>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
