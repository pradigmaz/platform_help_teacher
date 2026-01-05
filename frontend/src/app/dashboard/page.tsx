'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import {
  StudentAPI,
  StudentProfile,
  StudentAttendance,
  StudentLab,
  StudentAttestation,
  StudentTeacherContacts,
  TeacherContacts,
} from '@/lib/api';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { TextGenerateEffect } from '@/components/ui/text-generate-effect';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  IconCalendar,
  IconFlask,
  IconTrophy,
  IconChartBar,
  IconArrowRight,
  IconCheck,
  IconClock,
  IconX,
  IconAlertTriangle,
  IconSparkles,
  IconTargetArrow,
  IconBrandTelegram,
  IconBrandVk,
  IconMessage,
  IconUser,
} from '@tabler/icons-react';
import Link from 'next/link';
import { motion } from "motion/react";
import { cn } from '@/lib/utils';

export default function DashboardOverview() {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [attendance, setAttendance] = useState<StudentAttendance | null>(null);
  const [labs, setLabs] = useState<StudentLab[]>([]);
  const [attestation1, setAttestation1] = useState<StudentAttestation | null>(null);
  const [attestation2, setAttestation2] = useState<StudentAttestation | null>(null);
  const [teacherContacts, setTeacherContacts] = useState<StudentTeacherContacts | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [profileData, attendanceData, labsData, att1, att2, contacts] = await Promise.all([
          StudentAPI.getProfile(),
          StudentAPI.getAttendance(),
          StudentAPI.getLabs(),
          StudentAPI.getAttestation('first'),
          StudentAPI.getAttestation('second'),
          StudentAPI.getTeacherContacts().catch(() => null),
        ]);
        setProfile(profileData);
        setAttendance(attendanceData);
        setLabs(labsData);
        setAttestation1(att1);
        setAttestation2(att2);
        setTeacherContacts(contacts);
      } catch {
        toast.error('Ошибка загрузки данных');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) return <OverviewSkeleton />;

  const acceptedLabs = labs.filter((l) => l.submission?.status === 'ACCEPTED').length;
  const pendingLabs = labs.filter((l) => l.submission?.status === 'PENDING').length;
  const labsProgress = labs.length > 0 ? Math.round((acceptedLabs / labs.length) * 100) : 0;
  const attendanceRate = attendance?.stats.attendance_rate || 0;

  const firstName = profile?.full_name?.split(' ')[1] || 'Студент';

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="space-y-2">
        <TextGenerateEffect
          words={`Привет, ${firstName}!`}
          className="text-3xl font-bold"
          duration={0.3}
        />
        <p className="text-muted-foreground">
          Вот краткий обзор твоей успеваемости
        </p>
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Attendance Card - Large */}
        <CardSpotlight className="md:col-span-1 lg:row-span-2 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <IconCalendar className="h-6 w-6 text-blue-500" />
            </div>
            <Link
              href="/dashboard/attendance"
              className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1"
            >
              Подробнее <IconArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">Посещаемость</h3>
          
          {attendance && attendance.stats.total_classes > 0 ? (
            <div className="flex-1 flex flex-col justify-center">
              <div className="relative w-32 h-32 mx-auto mb-4">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="currentColor"
                    strokeWidth="12"
                    fill="none"
                    className="text-neutral-800"
                  />
                  <motion.circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="currentColor"
                    strokeWidth="12"
                    fill="none"
                    strokeLinecap="round"
                    className="text-blue-500"
                    initial={{ strokeDasharray: "0 352" }}
                    animate={{ strokeDasharray: `${attendanceRate * 3.52} 352` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-3xl font-bold text-foreground">{Math.round(attendanceRate)}%</span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-sm">
                <div>
                  <div className="flex items-center justify-center gap-1 text-green-500">
                    <IconCheck className="h-4 w-4" />
                    <span className="font-semibold">{attendance.stats.present}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">Был</p>
                </div>
                <div>
                  <div className="flex items-center justify-center gap-1 text-yellow-500">
                    <IconClock className="h-4 w-4" />
                    <span className="font-semibold">{attendance.stats.late}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">Опоздал</p>
                </div>
                <div>
                  <div className="flex items-center justify-center gap-1 text-red-500">
                    <IconX className="h-4 w-4" />
                    <span className="font-semibold">{attendance.stats.absent}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">Пропуск</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-muted-foreground text-sm">Нет данных о посещаемости</p>
            </div>
          )}
        </CardSpotlight>

        {/* Attestation Card - Enhanced with breakdown */}
        <CardSpotlight className="md:col-span-1 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-purple-500/10">
              <IconTrophy className="h-6 w-6 text-purple-500" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-4">Аттестация</h3>
          
          <Tabs defaultValue="first" className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="first">1-я аттестация</TabsTrigger>
              <TabsTrigger value="second">2-я аттестация</TabsTrigger>
            </TabsList>
            
            <TabsContent value="first">
              <AttestationBreakdown attestation={attestation1} />
            </TabsContent>
            
            <TabsContent value="second">
              <AttestationBreakdown attestation={attestation2} />
            </TabsContent>
          </Tabs>
        </CardSpotlight>

        {/* Labs Progress Card */}
        <CardSpotlight className="md:col-span-1 lg:col-span-1">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-green-500/10">
              <IconFlask className="h-6 w-6 text-green-500" />
            </div>
            <Link
              href="/dashboard/labs"
              className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1"
            >
              Все работы <IconArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-4">Лабораторные</h3>
          
          {labs.length > 0 ? (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-muted-foreground">Прогресс сдачи</span>
                  <span className="text-foreground font-medium">{acceptedLabs}/{labs.length}</span>
                </div>
                <Progress value={labsProgress} className="h-2" />
              </div>
              <div className="flex justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <span className="text-muted-foreground">Сдано: {acceptedLabs}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-yellow-500" />
                  <span className="text-muted-foreground">Проверка: {pendingLabs}</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">Нет лабораторных работ</p>
          )}
        </CardSpotlight>

        {/* Quick Stats Card */}
        <CardSpotlight className="md:col-span-2 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-lg bg-orange-500/10">
              <IconChartBar className="h-6 w-6 text-orange-500" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-4">Общая статистика</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatItem
              label="Всего занятий"
              value={attendance?.stats.total_classes || 0}
              color="blue"
            />
            <StatItem
              label="Всего лаб"
              value={labs.length}
              color="green"
            />
            <StatItem
              label="Средний балл"
              value={calculateAverageGrade(labs)}
              color="purple"
            />
            <StatItem
              label="Группа"
              value={profile?.group?.code || '—'}
              color="orange"
              isText
            />
          </div>
        </CardSpotlight>

        {/* Teacher Contact Card */}
        {teacherContacts?.contacts && Object.keys(teacherContacts.contacts).length > 0 && (
          <TeacherContactCard 
            contacts={teacherContacts.contacts} 
            teacherName={teacherContacts.teacher_name} 
          />
        )}
      </div>

      {/* Recent Labs */}
      {labs.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Последние лабораторные</h3>
            <Link
              href="/dashboard/labs"
              className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1"
            >
              Все работы <IconArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {labs.slice(0, 3).map((lab, idx) => (
              <motion.div
                key={lab.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="p-4 rounded-xl border border-border bg-card border-border hover:border-border/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-foreground text-sm truncate flex-1">
                    {lab.title}
                  </h4>
                  {lab.submission ? (
                    <Badge
                      variant={
                        lab.submission.status === 'ACCEPTED'
                          ? 'default'
                          : lab.submission.status === 'REJECTED'
                          ? 'destructive'
                          : 'secondary'
                      }
                      className="ml-2 text-xs"
                    >
                      {lab.submission.status === 'ACCEPTED'
                        ? 'Принято'
                        : lab.submission.status === 'REJECTED'
                        ? 'Отклонено'
                        : 'Проверка'}
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="ml-2 text-xs">
                      Не сдано
                    </Badge>
                  )}
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    Дедлайн: {lab.deadline ? new Date(lab.deadline).toLocaleDateString('ru-RU') : '—'}
                  </span>
                  <span className="font-medium">
                    {lab.submission?.grade !== undefined
                      ? `${lab.submission.grade}/${lab.max_grade}`
                      : `—/${lab.max_grade}`}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatItem({
  label,
  value,
  color,
  isText = false,
}: {
  label: string;
  value: number | string;
  color: 'blue' | 'green' | 'purple' | 'orange';
  isText?: boolean;
}) {
  const colorClasses = {
    blue: 'text-blue-500',
    green: 'text-green-500',
    purple: 'text-purple-500',
    orange: 'text-orange-500',
  };

  return (
    <div className="text-center p-3 rounded-lg bg-muted border border-border">
      <p className={`text-2xl font-bold ${colorClasses[color]}`}>
        {isText ? value : value}
      </p>
      <p className="text-xs text-muted-foreground mt-1">{label}</p>
    </div>
  );
}

function calculateAverageGrade(labs: StudentLab[]): string {
  const gradedLabs = labs.filter((l) => l.submission?.grade !== undefined);
  if (gradedLabs.length === 0) return '—';
  
  const total = gradedLabs.reduce((sum, lab) => {
    const grade = lab.submission?.grade || 0;
    const maxGrade = lab.max_grade || 1;
    return sum + (grade / maxGrade) * 100;
  }, 0);
  
  return Math.round(total / gradedLabs.length) + '%';
}

function OverviewSkeleton() {
  return (
    <div className="p-6 space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Skeleton className="h-[300px] rounded-xl" />
        <Skeleton className="h-[140px] rounded-xl" />
        <Skeleton className="h-[140px] rounded-xl" />
        <Skeleton className="h-[140px] md:col-span-2 rounded-xl" />
      </div>
    </div>
  );
}

// --- Attestation Breakdown Component ---

interface AttestationBreakdownProps {
  attestation: StudentAttestation | null;
}

function AttestationBreakdown({ attestation }: AttestationBreakdownProps) {
  if (!attestation || attestation.error) {
    return (
      <div className="text-center py-6 text-muted-foreground">
        <p>Данные аттестации недоступны</p>
      </div>
    );
  }

  const maxPoints = attestation.max_points || 40;
  const minPassing = attestation.min_passing_points || 18;
  const progressPercent = (attestation.total_score / maxPoints) * 100;
  const pointsToPass = minPassing - attestation.total_score;
  const isBorderline = !attestation.is_passing && pointsToPass <= 5;

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'отл': return 'bg-green-500 text-white';
      case 'хор': return 'bg-blue-500 text-white';
      case 'уд': return 'bg-yellow-500 text-white';
      case 'неуд': return 'bg-red-500 text-white';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  return (
    <div className="space-y-4">
      {/* Total Score */}
      <div className={cn(
        "p-4 rounded-lg border-2",
        attestation.is_passing ? "border-green-500/30 bg-green-500/5" : "border-red-500/30 bg-red-500/5"
      )}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {attestation.is_passing ? (
              <IconCheck className="h-5 w-5 text-green-500" />
            ) : (
              <IconX className="h-5 w-5 text-red-500" />
            )}
            <span className="font-medium">
              {attestation.is_passing ? 'Зачёт' : 'Незачёт'}
            </span>
          </div>
          <Badge className={getGradeColor(attestation.grade)}>
            {attestation.grade}
          </Badge>
        </div>
        
        <div className="text-center mb-2">
          <span className="text-3xl font-bold">{attestation.total_score.toFixed(1)}</span>
          <span className="text-lg text-muted-foreground">/{maxPoints}</span>
        </div>
        
        <Progress 
          value={progressPercent}
          className={cn(
            "h-2",
            attestation.is_passing ? "[&>div]:bg-green-500" : "[&>div]:bg-red-500"
          )}
        />
        
        <p className="text-xs text-center text-muted-foreground mt-2">
          Порог зачёта: {minPassing} баллов
        </p>
      </div>

      {/* Score Breakdown */}
      <div className="space-y-3">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          Разбивка баллов
        </p>
        
        {/* Labs */}
        <ScoreBreakdownItem
          icon={<IconFlask className="h-4 w-4" />}
          title="Лабораторные"
          score={attestation.lab_score || 0}
          maxScore={24}
          color="purple"
          details={attestation.breakdown?.labs ? (
            <span>
              Сдано: {attestation.breakdown.labs.count}/{attestation.breakdown.labs.required}
            </span>
          ) : undefined}
        />
        
        {/* Attendance */}
        <ScoreBreakdownItem
          icon={<IconCalendar className="h-4 w-4" />}
          title="Посещаемость"
          score={attestation.attendance_score || 0}
          maxScore={8}
          color="blue"
          details={attestation.breakdown?.attendance ? (
            <span>
              ✓ {attestation.breakdown.attendance.present} | 
              ⏰ {attestation.breakdown.attendance.late}
            </span>
          ) : undefined}
        />
        
        {/* Activity */}
        <ScoreBreakdownItem
          icon={<IconSparkles className="h-4 w-4" />}
          title="Активность"
          score={attestation.activity_score || 0}
          maxScore={8}
          color="amber"
          details={attestation.breakdown?.activity ? (
            <span>Начислено: {attestation.breakdown.activity.raw}</span>
          ) : undefined}
        />
      </div>

      {/* Recommendations for failing students */}
      {!attestation.is_passing && (
        <ImprovementRecommendations 
          pointsToPass={pointsToPass}
          isBorderline={isBorderline}
          breakdown={attestation.breakdown}
        />
      )}
    </div>
  );
}

// --- Score Breakdown Item ---

interface ScoreBreakdownItemProps {
  icon: React.ReactNode;
  title: string;
  score: number;
  maxScore: number;
  color: 'purple' | 'blue' | 'amber';
  details?: React.ReactNode;
}

function ScoreBreakdownItem({ icon, title, score, maxScore, color, details }: ScoreBreakdownItemProps) {
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
    <div className="flex items-center gap-3 p-2 rounded-lg bg-muted/50">
      <div className={cn("p-1.5 rounded-md", colorClasses[color])}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="font-medium">{title}</span>
          <span className="font-semibold">
            {score.toFixed(1)}
            <span className="text-muted-foreground font-normal">/{maxScore}</span>
          </span>
        </div>
        <Progress 
          value={maxScore > 0 ? (score / maxScore) * 100 : 0}
          className={cn("h-1", progressColors[color])}
        />
        {details && (
          <p className="text-xs text-muted-foreground mt-1">{details}</p>
        )}
      </div>
    </div>
  );
}

// --- Improvement Recommendations Component ---

interface ImprovementRecommendationsProps {
  pointsToPass: number;
  isBorderline: boolean;
  breakdown?: StudentAttestation['breakdown'];
}

function ImprovementRecommendations({ pointsToPass, isBorderline, breakdown }: ImprovementRecommendationsProps) {
  const recommendations: string[] = [];
  
  // Generate specific recommendations based on breakdown
  if (breakdown) {
    if (breakdown.labs && breakdown.labs.count < breakdown.labs.required) {
      const labsNeeded = breakdown.labs.required - breakdown.labs.count;
      recommendations.push(`Сдать ${labsNeeded} лабораторн${labsNeeded === 1 ? 'ую' : labsNeeded < 5 ? 'ые' : 'ых'} работ${labsNeeded === 1 ? 'у' : labsNeeded < 5 ? 'ы' : ''}`);
    }
    
    if (breakdown.attendance && breakdown.attendance.present < breakdown.attendance.total_classes * 0.8) {
      recommendations.push('Улучшить посещаемость занятий');
    }
    
    if (breakdown.activity && breakdown.activity.raw < 4) {
      recommendations.push('Получить баллы за активность на занятиях');
    }
  }
  
  // Default recommendations if none generated
  if (recommendations.length === 0) {
    recommendations.push('Сдать недостающие лабораторные работы');
    recommendations.push('Получить баллы за активность');
    recommendations.push('Улучшить посещаемость');
  }

  return (
    <div className={cn(
      "p-3 rounded-lg border",
      isBorderline 
        ? "border-yellow-500/30 bg-yellow-500/5" 
        : "border-red-500/30 bg-red-500/5"
    )}>
      <div className="flex items-start gap-2">
        <div className={cn(
          "p-1.5 rounded-md shrink-0",
          isBorderline ? "bg-yellow-500/20" : "bg-red-500/20"
        )}>
          {isBorderline ? (
            <IconAlertTriangle className={cn("h-4 w-4", "text-yellow-600")} />
          ) : (
            <IconTargetArrow className={cn("h-4 w-4", "text-red-600")} />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className={cn(
            "font-medium text-sm",
            isBorderline ? "text-yellow-600" : "text-red-600"
          )}>
            {isBorderline ? 'Почти зачёт!' : 'Как улучшить результат'}
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            До зачёта не хватает <span className="font-semibold">{pointsToPass.toFixed(1)} баллов</span>
          </p>
          
          <ul className="text-xs text-muted-foreground mt-2 space-y-1">
            {recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-1.5">
                <span className="text-primary mt-0.5">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

// --- Teacher Contact Card Component ---

interface TeacherContactCardProps {
  contacts: TeacherContacts;
  teacherName?: string;
}

function TeacherContactCard({ contacts, teacherName }: TeacherContactCardProps) {
  const hasContacts = contacts && Object.values(contacts).some(v => v);
  
  if (!hasContacts) {
    return null;
  }

  return (
    <CardSpotlight className="md:col-span-1">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 rounded-lg bg-cyan-500/10">
          <IconUser className="h-6 w-6 text-cyan-500" />
        </div>
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-2">Преподаватель</h3>
      {teacherName && (
        <p className="text-sm text-muted-foreground mb-4">{teacherName}</p>
      )}
      
      <div className="space-y-2">
        {contacts.telegram && (
          <ContactLink
            icon={<IconBrandTelegram className="h-4 w-4" />}
            href={`https://t.me/${contacts.telegram.replace('@', '')}`}
            label={contacts.telegram}
            color="blue"
          />
        )}
        {contacts.vk && (
          <ContactLink
            icon={<IconBrandVk className="h-4 w-4" />}
            href={contacts.vk.startsWith('http') ? contacts.vk : `https://vk.com/${contacts.vk}`}
            label={contacts.vk}
            color="blue"
          />
        )}
        {contacts.max && (
          <ContactLink
            icon={<IconMessage className="h-4 w-4" />}
            href={contacts.max.startsWith('http') ? contacts.max : `https://max.ru/${contacts.max}`}
            label={contacts.max}
            color="green"
          />
        )}
      </div>
    </CardSpotlight>
  );
}

interface ContactLinkProps {
  icon: React.ReactNode;
  href: string;
  label: string;
  color: 'blue' | 'green';
}

function ContactLink({ icon, href, label, color }: ContactLinkProps) {
  const colorClasses = {
    blue: 'text-blue-500 hover:text-blue-400',
    green: 'text-green-500 hover:text-green-400',
  };

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "flex items-center gap-2 text-sm transition-colors",
        colorClasses[color]
      )}
    >
      {icon}
      <span className="truncate">{label}</span>
    </a>
  );
}
