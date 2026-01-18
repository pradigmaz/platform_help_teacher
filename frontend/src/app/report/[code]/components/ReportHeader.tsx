'use client';

import { Badge } from '@/components/ui/badge';
import { 
  BookOpen, 
  MessageCircle,
} from 'lucide-react';
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
    <div className="space-y-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 p-6 rounded-xl border shadow-sm">
      {/* Title */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="text-4xl">📊</div>
        <div className="flex-1">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-800 dark:text-gray-100 leading-tight">
            Академический отчёт
          </h1>
          <p className="text-xl sm:text-2xl text-gray-600 dark:text-gray-300 mt-1">
            Группа {formatGroupCode(data.group_code)} • {data.total_students} {getStudentWord(data.total_students)}
          </p>
        </div>
        <Badge variant="secondary" className="text-base px-4 py-2 font-semibold">
          {reportTypeLabels[data.report_type]}
        </Badge>
      </div>

      {/* Subject info */}
      {data.subject_name && (
        <div className="flex items-center gap-3 text-lg text-gray-700 dark:text-gray-300 bg-white/50 dark:bg-gray-800/50 p-4 rounded-lg">
          <BookOpen className="h-6 w-6 text-blue-600" />
          <span className="font-medium">{data.subject_name}</span>
        </div>
      )}

      {/* Teacher Contacts */}
      {hasContacts && (
        <div className="bg-white/70 dark:bg-gray-800/70 p-4 rounded-lg border">
          <p className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
            📞 Связь с преподавателем
          </p>
          <div className="flex flex-wrap gap-4 text-base">
            {contacts?.telegram && (
              <a
                href={`https://t.me/${contacts.telegram.replace('@', '')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-blue-600 hover:text-blue-500 transition-colors bg-blue-50 dark:bg-blue-900/30 px-3 py-2 rounded-lg font-medium"
              >
                <MessageCircle className="h-5 w-5" />
                <span>Telegram: {contacts.telegram}</span>
              </a>
            )}
            {contacts?.vk && (
              <a
                href={contacts.vk.startsWith('http') ? contacts.vk : `https://vk.com/${contacts.vk}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-blue-600 hover:text-blue-500 transition-colors bg-blue-50 dark:bg-blue-900/30 px-3 py-2 rounded-lg font-medium"
              >
                <MessageCircle className="h-5 w-5" />
                <span>ВКонтакте</span>
              </a>
            )}
            {contacts?.max && (
              <a
                href={contacts.max.startsWith('http') ? contacts.max : `https://max.ru/${contacts.max}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-green-600 hover:text-green-500 transition-colors bg-green-50 dark:bg-green-900/30 px-3 py-2 rounded-lg font-medium"
              >
                <MessageCircle className="h-5 w-5" />
                <span>MAX</span>
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}