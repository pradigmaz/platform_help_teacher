'use client';

import { Badge } from '@/components/ui/badge';
import { 
  BookOpen, 
  MessageCircle,
} from 'lucide-react';
import { PublicReportData, ReportType } from '@/lib/api';
import { formatGroupCode } from '@/lib/utils';

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
    <div className="space-y-4">
      {/* Title */}
      <div className="flex items-center gap-2 flex-wrap">
        <h1 className="text-2xl sm:text-3xl font-bold">
          Отчёт группы {formatGroupCode(data.group_code)}
          <span className="text-muted-foreground font-normal text-xl sm:text-2xl ml-2">
            ({data.total_students} студентов)
          </span>
        </h1>
        <Badge variant="secondary">{reportTypeLabels[data.report_type]}</Badge>
      </div>

      {/* Subject info */}
      {data.subject_name && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <BookOpen className="h-4 w-4" />
          <span>{data.subject_name}</span>
        </div>
      )}

      {/* Teacher Contacts */}
      {hasContacts && (
        <div className="pt-2 border-t">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
            Контакты преподавателя
          </p>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm">
            {contacts?.telegram && (
              <a
                href={`https://t.me/${contacts.telegram.replace('@', '')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-blue-600 hover:text-blue-500 transition-colors"
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
                className="flex items-center gap-1.5 text-blue-600 hover:text-blue-500 transition-colors"
              >
                <MessageCircle className="h-4 w-4" />
                <span>VK</span>
              </a>
            )}
            {contacts?.max && (
              <a
                href={contacts.max.startsWith('http') ? contacts.max : `https://max.ru/${contacts.max}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-green-600 hover:text-green-500 transition-colors"
              >
                <MessageCircle className="h-4 w-4" />
                <span>MAX</span>
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
