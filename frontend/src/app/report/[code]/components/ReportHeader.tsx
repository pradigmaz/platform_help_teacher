'use client';

import { Badge } from '@/components/ui/badge';
import { BookOpen, GraduationCap, MessageCircle, Users } from 'lucide-react';
import { PublicReportData, ReportType } from '@/lib/api';
import { formatGroupCode } from '@/lib/utils';
import { getStudentWord } from '@/lib/utils/pluralize';

interface ReportHeaderProps {
  data: PublicReportData;
}

const reportTypeLabels: Record<ReportType, string> = {
  full: 'Полный отчёт',
  attestation_only: 'Только аттестация',
  attendance_only: 'Только посещаемость',
};

export function ReportHeader({ data }: ReportHeaderProps) {
  const contacts = data.teacher_contacts;
  const hasContacts = contacts && Object.values(contacts).some(v => v);

  return (
    <section className="rounded-3xl border border-border/60 bg-card/95 p-5 shadow-sm sm:p-6">
      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <GraduationCap className="h-4 w-4" />
              <span>Публичный отчёт группы</span>
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Группа {formatGroupCode(data.group_code)}
              </h1>
              <p className="text-base text-muted-foreground sm:text-lg">
                Академический отчёт по группе с общими показателями и списком студентов
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="px-3 py-1.5 text-sm font-medium">
              {reportTypeLabels[data.report_type]}
            </Badge>
            {data.subject_name && (
              <Badge variant="outline" className="px-3 py-1.5 text-sm font-medium">
                {data.subject_name}
              </Badge>
            )}
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <div className="rounded-2xl border border-border/60 bg-background/80 p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Users className="h-4 w-4" />
              <span>Состав группы</span>
            </div>
            <p className="mt-2 text-2xl font-semibold">
              {data.total_students} {getStudentWord(data.total_students)}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Данные ниже можно смотреть по всей группе или по подгруппам
            </p>
          </div>

          {data.subject_name && (
            <div className="rounded-2xl border border-border/60 bg-background/80 p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <BookOpen className="h-4 w-4" />
                <span>Предмет</span>
              </div>
              <p className="mt-2 text-lg font-semibold">{data.subject_name}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Тип отчёта: {reportTypeLabels[data.report_type].toLowerCase()}
              </p>
            </div>
          )}

          {hasContacts && (
            <div className="rounded-2xl border border-border/60 bg-background/80 p-4">
              <p className="text-sm text-muted-foreground">Связь с преподавателем</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {contacts?.telegram && (
                  <a
                    href={`https://t.me/${contacts.telegram.replace('@', '')}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-full border border-border/60 px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
                  >
                    <MessageCircle className="h-4 w-4" />
                    <span>{contacts.telegram}</span>
                  </a>
                )}
                {contacts?.vk && (
                  <a
                    href={contacts.vk.startsWith('http') ? contacts.vk : `https://vk.com/${contacts.vk}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-full border border-border/60 px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
                  >
                    <MessageCircle className="h-4 w-4" />
                    <span>ВКонтакте</span>
                  </a>
                )}
                {contacts?.max && (
                  <a
                    href={contacts.max.startsWith('http') ? contacts.max : `https://max.ru/${contacts.max}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-full border border-border/60 px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
                  >
                    <MessageCircle className="h-4 w-4" />
                    <span>MAX</span>
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
