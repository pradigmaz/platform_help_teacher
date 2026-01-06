'use client';

import { useState } from 'react';
import { Copy, RefreshCw, Key, Check, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MagicCard } from '@/components/ui/magic-card';
import { toast } from '@/components/ui/sonner';
import type { StudentInGroup } from '@/lib/api/types';

interface CodesTabProps {
  students: StudentInGroup[];
  searchQuery: string;
  groupInviteCode?: string;
  onGenerateCodes: () => Promise<void>;
  onRegenerateCode: (userId: string) => Promise<void>;
  onRegenerateGroupCode: () => Promise<void>;
  isGenerating: boolean;
  isRegeneratingGroupCode: boolean;
}

export function CodesTab({
  students,
  searchQuery,
  groupInviteCode,
  onGenerateCodes,
  onRegenerateCode,
  onRegenerateGroupCode,
  isGenerating,
  isRegeneratingGroupCode,
}: CodesTabProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [copiedGroupCode, setCopiedGroupCode] = useState(false);

  const filteredStudents = students
    .filter(student => student.full_name.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => a.full_name.localeCompare(b.full_name, 'ru'));

  const studentsWithoutCode = students.filter(s => !s.invite_code).length;

  const copyGroupCode = () => {
    if (!groupInviteCode) return;
    navigator.clipboard.writeText(groupInviteCode);
    setCopiedGroupCode(true);
    toast.success('Код группы скопирован');
    setTimeout(() => setCopiedGroupCode(false), 2000);
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Групповой код */}
      <div className="p-4 bg-card border rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Групповой код для бота</p>
            <p className="text-sm text-muted-foreground">
              Студенты вводят этот код в боте, затем своё ФИО
            </p>
          </div>
          <div className="flex items-center gap-3">
            {groupInviteCode ? (
              <code className="bg-primary/10 text-primary px-4 py-2 rounded-lg font-mono text-lg font-bold">
                {groupInviteCode}
              </code>
            ) : (
              <span className="text-muted-foreground italic">Не сгенерирован</span>
            )}
            <Button 
              variant="outline" 
              onClick={copyGroupCode}
              className="gap-2"
              disabled={!groupInviteCode}
            >
              {copiedGroupCode ? (
                <>
                  <Check className="w-4 h-4 text-green-500" />
                  Скопировано
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Копировать
                </>
              )}
            </Button>
            <Button 
              variant="outline"
              onClick={onRegenerateGroupCode}
              disabled={isRegeneratingGroupCode}
              className="gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${isRegeneratingGroupCode ? 'animate-spin' : ''}`} />
              {groupInviteCode ? 'Обновить' : 'Сгенерировать'}
            </Button>
          </div>
        </div>
      </div>

      {/* Индивидуальные коды */}
      <div className="p-4 bg-card border rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Индивидуальные инвайт-коды</p>
            <p className="text-sm text-muted-foreground">
              Персональные коды для прямой привязки без ввода ФИО
              <span className="mx-2">•</span>
              Без кода: <span className="font-medium text-orange-500">{studentsWithoutCode}</span>
            </p>
          </div>
          <Button onClick={onGenerateCodes} disabled={isGenerating || studentsWithoutCode === 0}>
            <Key className="w-4 h-4 mr-2" />
            {isGenerating ? 'Генерация...' : 'Сгенерировать'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredStudents.length === 0 ? (
          <div className="col-span-full py-12 text-center text-muted-foreground border rounded-xl bg-card/50">
            {searchQuery ? 'Студенты не найдены' : 'В группе пока нет студентов'}
          </div>
        ) : (
          filteredStudents.map((student) => (
            <MagicCard
              key={student.id}
              className="p-4 flex flex-col gap-3"
              gradientColor="rgba(59, 130, 246, 0.1)"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-full">
                    <User className="w-4 h-4 text-primary" />
                  </div>
                  <div className="font-medium truncate max-w-[150px]" title={student.full_name}>
                    {student.full_name}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8 w-8 p-0"
                  onClick={() => onRegenerateCode(student.id)}
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </Button>
              </div>

              <div className="mt-auto pt-3 border-t flex items-center justify-between">
                {student.invite_code ? (
                  <>
                    <code className="bg-muted px-2 py-1 rounded font-mono text-sm text-primary font-bold">
                      {student.invite_code}
                    </code>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-8 gap-2"
                      onClick={() => copyToClipboard(student.invite_code!, student.id)}
                    >
                      {copiedId === student.id ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-green-500" />
                          <span>Ок</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Копировать</span>
                        </>
                      )}
                    </Button>
                  </>
                ) : (
                  <span className="text-muted-foreground text-xs italic">Код не сгенерирован</span>
                )}
              </div>
            </MagicCard>
          ))
        )}
      </div>
    </div>
  );
}
