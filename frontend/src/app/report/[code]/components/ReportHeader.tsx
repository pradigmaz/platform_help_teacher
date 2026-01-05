'use client';

import { Badge } from '@/components/ui/badge';
import { 
  Users, 
  BookOpen, 
  GraduationCap,
  Calendar,
  MessageCircle,
} from 'lucide-react';
import { PublicReportData, ReportType } from '@/lib/api';

interface ReportHeaderProps {
  data: PublicReportData;
}

const reportTypeLabels: Record<ReportType, string> = {
  full: 'Полный отчёт',
  attestation_only: 'Только аттестация',
  attendance_only: 'Только посещаемость',
};

// Format group code: ИС1231ОТ -> ИС1-231-ОТ
function formatGroupCode(code: string): string {
  // Pattern: 2-3 letters + 1 digit + 3 digits + 2 letters (suffix)
  const match = code.match(/^([А-ЯA-Z]{2,3})(\d)(\d{3})([А-ЯA-Z]{2})$/i);
  if (match) {
    return `${match[1]}${match[2]}-${match[3]}-${match[4]}`;
  }
  return code;
}

export function ReportHeader({ data }: ReportHeaderProps) {
  const generatedDate = new Date(data.generated_at).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const contacts = data.teacher_contacts;
  const hasContacts = contacts && Object.values(contacts).some(v => v);

  return (
    <div className="space-y-4">
      {/* Title */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 flex-wrap">
          <h1 className="text-2xl sm:text-3xl font-bold">
            Отчёт группы {formatGroupCode(data.group_code)}
          </h1>
          <Badge variant="secondary">{reportTypeLabels[data.report_type]}</Badge>
        </div>
        {data.group_name && (
          <p className="text-lg text-muted-foreground">{data.group_name}</p>
        )}
      </div>

      {/* Info Cards */}
      <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
        {data.subject_name && (
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            <span>{data.subject_name}</span>
          </div>
        )}
        <div className="flex items-center gap-2">
          <GraduationCap className="h-4 w-4" />
          <span>{data.teacher_name}</span>
        </div>
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4" />
          <span>{data.total_students} студентов</span>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4" />
          <span>Сформирован: {generatedDate}</span>
        </div>
      </div>

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
