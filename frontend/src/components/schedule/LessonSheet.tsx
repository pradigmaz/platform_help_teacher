'use client';

import { useState, useEffect, useCallback } from 'react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { X, Save, BookOpen, Users, Check, Clock, HelpCircle, XCircle, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { NoteButton } from '@/components/notes';

// Types
interface Student {
  id: string;
  full_name: string;
}

export interface LessonData {
  id: string;
  date: string;
  lesson_number: number;
  lesson_type: string;
  topic: string | null;
  subject_name: string | null;
  work_number: number | null;
  subgroup: number | null;
  is_cancelled: boolean;
  ended_early?: boolean;
  group_id?: string;
  group_name?: string;
}

interface LessonSheetProps {
  lesson: LessonData | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: () => void;
}

type LessonStatus = 'normal' | 'cancelled' | 'early';
type AttendanceStatus = 'PRESENT' | 'LATE' | 'EXCUSED' | 'ABSENT';

const LESSON_TIMES = [
  '08:00–09:30', '09:40–11:10', '11:20–12:50', '13:20–14:50',
  '15:00–16:30', '16:40–18:10', '18:20–19:50', '20:00–21:30'
];

const TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  lecture: { label: 'Лекция', color: 'bg-blue-500/15 text-blue-400 border-blue-500/20' },
  lab: { label: 'Лаб. работа', color: 'bg-purple-500/15 text-purple-400 border-purple-500/20' },
  practice: { label: 'Практика', color: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20' },
};

const ATTENDANCE_CONFIG: Record<AttendanceStatus, { icon: typeof Check; color: string; bg: string; label: string }> = {
  PRESENT: { icon: Check, color: 'text-emerald-500', bg: 'bg-emerald-500/15', label: 'Присутствует' },
  LATE: { icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-500/15', label: 'Опоздал' },
  EXCUSED: { icon: HelpCircle, color: 'text-blue-500', bg: 'bg-blue-500/15', label: 'Уваж. причина' },
  ABSENT: { icon: XCircle, color: 'text-rose-500', bg: 'bg-rose-500/15', label: 'Отсутствует' },
};

const CYCLE_ORDER: AttendanceStatus[] = ['PRESENT', 'LATE', 'EXCUSED', 'ABSENT'];


export function LessonSheet({ lesson, isOpen, onClose, onSave }: LessonSheetProps) {
  const [students, setStudents] = useState<Student[]>([]);
  const [attendance, setAttendance] = useState<Record<string, AttendanceStatus | null>>({});
  const [grades, setGrades] = useState<Record<string, number | null>>({});
  const [topic, setTopic] = useState('');
  const [status, setStatus] = useState<LessonStatus>('normal');
  const [isLoading, setIsLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Load data when lesson changes
  useEffect(() => {
    if (lesson && isOpen) {
      loadLessonData();
    }
  }, [lesson?.id, isOpen]);

  const loadLessonData = useCallback(async () => {
    if (!lesson) return;
    setIsLoading(true);

    try {
      // Load students from group if group_id exists
      if (lesson.group_id) {
        try {
          const { data: groupData } = await api.get(`/groups/${lesson.group_id}`);
          setStudents(groupData.students || []);
        } catch {
          // Fallback: try to get students from attendance data
          console.warn('Could not load group, trying attendance endpoint');
          setStudents([]);
        }
      }

      // Load attendance
      if (lesson.group_id) {
        const { data: attData } = await api.get('/admin/journal/attendance', {
          params: { group_id: lesson.group_id, lesson_ids: [lesson.id] }
        });
        const attMap: Record<string, AttendanceStatus | null> = {};
        for (const a of attData) {
          attMap[a.student_id] = a.status as AttendanceStatus;
        }
        setAttendance(attMap);
      }

      // Load grades
      const { data: gradeData } = await api.get('/admin/journal/grades', {
        params: { lesson_ids: [lesson.id] }
      });
      const gradeMap: Record<string, number | null> = {};
      for (const g of gradeData) {
        gradeMap[g.student_id] = g.grade;
      }
      setGrades(gradeMap);

      // Set topic and status
      setTopic(lesson.topic || '');
      setStatus(lesson.is_cancelled ? 'cancelled' : lesson.ended_early ? 'early' : 'normal');
      setHasChanges(false);
    } catch (err) {
      console.error('Ошибка загрузки данных занятия', err);
    } finally {
      setIsLoading(false);
    }
  }, [lesson]);

  const cycleAttendance = (studentId: string) => {
    setAttendance(prev => {
      const current = prev[studentId];
      if (!current) return { ...prev, [studentId]: 'PRESENT' };
      const idx = CYCLE_ORDER.indexOf(current);
      const next = CYCLE_ORDER[(idx + 1) % CYCLE_ORDER.length];
      return { ...prev, [studentId]: next };
    });
    setHasChanges(true);
  };

  const setGrade = (studentId: string, grade: number) => {
    setGrades(prev => ({
      ...prev,
      [studentId]: prev[studentId] === grade ? null : grade
    }));
    // Auto-set attendance if not set
    if (!attendance[studentId]) {
      setAttendance(prev => ({ ...prev, [studentId]: 'PRESENT' }));
    }
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!lesson) return;
    setIsLoading(true);

    try {
      // Save attendance
      const attRecords = Object.entries(attendance)
        .filter(([_, status]) => status)
        .map(([student_id, status]) => ({ student_id, status }));
      
      if (attRecords.length > 0) {
        await api.post('/admin/journal/attendance/bulk', {
          lesson_id: lesson.id,
          records: attRecords
        });
      }

      // Save grades
      for (const [student_id, grade] of Object.entries(grades)) {
        if (grade) {
          await api.post('/admin/journal/grades', {
            lesson_id: lesson.id,
            student_id,
            grade,
            work_number: lesson.work_number
          });
        }
      }

      // Save status
      if (status !== 'normal' || lesson.is_cancelled || lesson.ended_early) {
        await api.patch(`/admin/schedule/lessons/${lesson.id}`, {
          is_cancelled: status === 'cancelled',
          ended_early: status === 'early'
        });
      }

      // Save topic if changed
      if (topic !== (lesson.topic || '')) {
        await api.patch(`/admin/schedule/lessons/${lesson.id}`, { topic });
      }

      setHasChanges(false);
      onSave?.();
      onClose();
    } catch (err) {
      console.error('Ошибка сохранения', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!lesson) return null;

  const typeConfig = TYPE_CONFIG[lesson.lesson_type.toLowerCase()] || TYPE_CONFIG.lecture;
  const timeSlot = LESSON_TIMES[lesson.lesson_number - 1] || '';
  const canHaveGrade = ['lab', 'practice'].includes(lesson.lesson_type.toLowerCase());

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          'fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={onClose}
      />

      {/* Sheet */}
      <div
        className={cn(
          'fixed right-0 top-0 z-50 h-full w-[450px] bg-background border-l shadow-2xl',
          'transform transition-transform duration-300 ease-out flex flex-col',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="flex-none p-5 border-b bg-muted/30">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2 text-muted-foreground text-xs">
              <Calendar className="h-3 w-3" />
              <span>{format(new Date(lesson.date), 'EEEE, d MMMM', { locale: ru })}</span>
              <span>•</span>
              <span>{lesson.lesson_number} пара ({timeSlot})</span>
            </div>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">{lesson.group_name || 'Группа'}</h2>
            <Badge className={cn('border', typeConfig.color)}>{typeConfig.label}</Badge>
          </div>
          {lesson.subgroup && (
            <div className="text-sm text-muted-foreground mt-1">{lesson.subgroup} подгруппа</div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Status */}
          <div className="space-y-2">
            <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Статус занятия
            </Label>
            <div className="flex p-1 bg-muted rounded-lg">
              {([
                { id: 'normal', label: 'Обычное' },
                { id: 'cancelled', label: 'Отменено' },
                { id: 'early', label: 'Отпустил' }
              ] as const).map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => { setStatus(opt.id); setHasChanges(true); }}
                  className={cn(
                    'flex-1 py-1.5 text-xs font-medium rounded-md transition-all',
                    status === opt.id
                      ? 'bg-background text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Topic */}
          <div className="space-y-2">
            <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Тема занятия
            </Label>
            <div className="flex items-center gap-2 text-sm text-muted-foreground px-3 py-2 bg-muted rounded-md">
              <BookOpen className="h-4 w-4" />
              {lesson.subject_name || 'Предмет'}
            </div>
            <div className="relative">
              <Input
                value={topic}
                onChange={(e) => { setTopic(e.target.value); setHasChanges(true); }}
                placeholder="Введите тему занятия..."
                className="pr-16"
              />
              {canHaveGrade && lesson.work_number && (
                <div className="absolute right-2 top-1/2 -translate-y-1/2 bg-muted text-muted-foreground text-[10px] px-1.5 py-0.5 rounded">
                  ЛР №{lesson.work_number}
                </div>
              )}
            </div>
            <div className="flex justify-end">
              <NoteButton entityType="lesson" entityId={lesson.id} size="md" />
            </div>
          </div>

          {/* Students */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Users className="h-3 w-3" />
                Студенты ({students.length})
              </Label>
              <div className="flex gap-2 text-[10px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" /> Присут.
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-rose-500" /> Н/Б
                </span>
              </div>
            </div>

            <div className="border rounded-lg overflow-hidden">
              {/* Table header */}
              <div className="grid grid-cols-[32px_1fr_32px_40px_100px] gap-2 px-3 py-2 bg-muted text-[10px] font-medium text-muted-foreground uppercase">
                <span>#</span>
                <span>ФИО</span>
                <span></span>
                <span className="text-center">Посещ.</span>
                <span className="text-center">Оценка</span>
              </div>

              {/* Rows */}
              <div className="divide-y max-h-[340px] overflow-y-auto">
                {isLoading ? (
                  <div className="p-8 text-center text-muted-foreground text-sm">Загрузка...</div>
                ) : (
                  students.map((student, idx) => {
                    const att = attendance[student.id];
                    const attConfig = att ? ATTENDANCE_CONFIG[att] : null;
                    const AttIcon = attConfig?.icon;
                    const grade = grades[student.id];

                    return (
                      <div
                        key={student.id}
                        className={cn(
                          'grid grid-cols-[32px_1fr_32px_40px_100px] gap-2 px-3 py-2 items-center text-sm group',
                          idx % 2 === 0 ? 'bg-background' : 'bg-muted/30'
                        )}
                      >
                        <span className="text-muted-foreground text-xs">{idx + 1}</span>
                        <span className="truncate" title={student.full_name}>{student.full_name}</span>
                        <NoteButton entityType="student" entityId={student.id} size="sm" />
                        <button
                          onClick={() => cycleAttendance(student.id)}
                          className={cn(
                            'h-7 w-7 rounded-full flex items-center justify-center transition-all hover:scale-110 mx-auto',
                            attConfig ? `${attConfig.color} ${attConfig.bg}` : 'text-muted-foreground/50'
                          )}
                          title={attConfig?.label || 'Не отмечено'}
                        >
                          {AttIcon ? <AttIcon className="h-4 w-4" /> : <span>—</span>}
                        </button>
                        <div className="flex justify-center gap-1 opacity-50 group-hover:opacity-100 transition-opacity">
                          {canHaveGrade && [2, 3, 4, 5].map((g) => (
                            <button
                              key={g}
                              onClick={() => setGrade(student.id, g)}
                              className={cn(
                                'w-6 h-6 rounded text-xs font-bold transition-all',
                                grade === g
                                  ? 'bg-primary text-primary-foreground scale-110'
                                  : 'bg-muted text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                              )}
                            >
                              {g}
                            </button>
                          ))}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex-none p-4 border-t flex gap-3">
          <Button variant="outline" onClick={onClose}>Отмена</Button>
          <Button 
            className="flex-1" 
            onClick={handleSave}
            disabled={isLoading || !hasChanges}
          >
            <Save className="h-4 w-4 mr-2" />
            {hasChanges ? 'Сохранить изменения' : 'Сохранено'}
          </Button>
        </div>
      </div>
    </>
  );
}
