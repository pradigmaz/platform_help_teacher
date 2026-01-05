'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Users, TrendingUp, Award, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { AttendanceCell } from './AttendanceCell';
import { GradeCell } from './GradeCell';
import { NoteButton } from '@/components/notes';
import { AddActivityDialog } from '@/components/admin/AddActivityDialog';
import { LESSON_TYPE_INFO, canHaveGrade } from '../lib/journal-constants';
import type { Lesson, Student, GradeData } from '../lib/journal-constants';
import type { AttestationResult, AttestationType } from '@/lib/api';

interface JournalTableProps {
  lessons: Lesson[];
  students: Student[];
  attendance: Record<string, Record<string, string>>;
  grades: Record<string, Record<string, GradeData>>;
  attestationScores?: Record<string, AttestationResult>;
  attestationPeriod?: 'first' | 'second';
  onAttendanceChange: (lessonId: string, studentId: string, status: string) => void;
  onGradeChange: (lessonId: string, studentId: string, grade: number, workNumber: number | null) => void;
  onLessonClick?: (lesson: Lesson) => void;
  onStudentAttestationClick?: (student: Student, attestation: AttestationResult) => void;
  onActivityAdded?: () => void;
}

// Helper to get grade color based on grade string
function getGradeColor(grade: string): string {
  switch (grade) {
    case 'отл':
      return 'text-green-600 bg-green-50 dark:bg-green-950/30';
    case 'хор':
      return 'text-blue-600 bg-blue-50 dark:bg-blue-950/30';
    case 'уд':
      return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950/30';
    case 'неуд':
      return 'text-red-600 bg-red-50 dark:bg-red-950/30';
    default:
      return 'text-muted-foreground';
  }
}

export function JournalTable({
  lessons,
  students,
  attendance,
  grades,
  attestationScores,
  attestationPeriod,
  onAttendanceChange,
  onGradeChange,
  onLessonClick,
  onStudentAttestationClick,
  onActivityAdded,
}: JournalTableProps) {
  const [activityDialogOpen, setActivityDialogOpen] = useState(false);
  const [selectedStudentForActivity, setSelectedStudentForActivity] = useState<Student | null>(null);
  
  const sortedLessons = [...lessons].sort((a, b) => {
    const dateCompare = a.date.localeCompare(b.date);
    if (dateCompare !== 0) return dateCompare;
    return a.lesson_number - b.lesson_number;
  });

  // Calculate max work numbers per lesson type
  const getMaxWorkNum = (lessonType: string) => {
    return sortedLessons
      .filter(l => l.lesson_type.toLowerCase() === lessonType.toLowerCase() && l.work_number)
      .reduce((max, l) => Math.max(max, l.work_number || 0), 0);
  };

  return (
    <div className="relative overflow-auto max-h-[70vh] rounded-lg border">
      <Table>
        <TableHeader className="sticky top-0 z-20 bg-muted/95 backdrop-blur supports-[backdrop-filter]:bg-muted/80">
          <TableRow className="hover:bg-transparent">
            <TableHead className="sticky left-0 z-30 bg-muted/95 backdrop-blur min-w-[220px] font-semibold border-r">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                Студент
              </div>
            </TableHead>
            {sortedLessons.map(lesson => {
              const typeInfo = LESSON_TYPE_INFO[lesson.lesson_type] || LESSON_TYPE_INFO.LECTURE;
              const Icon = typeInfo.icon;
              return (
                <TableHead 
                  key={lesson.id} 
                  className="text-center min-w-[70px] px-2 cursor-pointer hover:bg-accent/50 transition-colors"
                  onClick={() => onLessonClick?.(lesson)}
                >
                  <div className="flex flex-col items-center gap-0.5">
                    <span className="text-[10px] text-muted-foreground">
                      {format(new Date(lesson.date), 'EEE', { locale: ru })}
                    </span>
                    <span className="text-xs font-medium">
                      {format(new Date(lesson.date), 'dd.MM')}
                    </span>
                    <Badge 
                      variant="secondary" 
                      className={`text-[10px] px-1.5 py-0 ${typeInfo.color} text-white`}
                    >
                      <Icon className="w-3 h-3 mr-0.5" />
                      {typeInfo.short}{lesson.work_number ? `${lesson.work_number}` : ''}
                    </Badge>
                  </div>
                </TableHead>
              );
            })}
            {attestationScores && (
              <TableHead className="text-center min-w-[80px] font-semibold border-l">
                <div className="flex flex-col items-center">
                  <Award className="w-4 h-4" />
                  <span className="text-[10px]">ИТОГО</span>
                </div>
              </TableHead>
            )}
            <TableHead className="sticky right-0 z-30 bg-muted/95 backdrop-blur text-center min-w-[60px] font-semibold border-l">
              <div className="flex flex-col items-center">
                <TrendingUp className="w-4 h-4" />
                <span className="text-[10px]">%</span>
              </div>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students.map((student, idx) => {
            let present = 0, total = 0;
            for (const lesson of sortedLessons) {
              const status = attendance[lesson.id]?.[student.id];
              if (status) {
                total++;
                if (status === 'PRESENT' || status === 'LATE') present++;
              }
            }
            const percentage = total > 0 ? Math.round(present / total * 100) : null;
            const isEven = idx % 2 === 0;

            return (
              <TableRow 
                key={student.id} 
                className={`${isEven ? 'bg-background' : 'bg-muted/30'} hover:bg-accent/50 transition-colors`}
              >
                <TableCell className={`sticky left-0 z-10 font-medium border-r ${isEven ? 'bg-background' : 'bg-muted/30'} hover:bg-accent/50`}>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground text-xs w-5">{idx + 1}.</span>
                    <span className="truncate max-w-[140px]" title={student.full_name}>
                      {student.full_name}
                    </span>
                    <div className="flex items-center gap-0.5 ml-auto">
                      <NoteButton entityType="student" entityId={student.id} size="sm" />
                      {attestationPeriod && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6 text-muted-foreground hover:text-primary"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedStudentForActivity(student);
                                  setActivityDialogOpen(true);
                                }}
                              >
                                <Sparkles className="h-3.5 w-3.5" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent side="right">
                              <p>Добавить активность</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                    </div>
                  </div>
                </TableCell>
                {sortedLessons.map(lesson => {
                  const status = attendance[lesson.id]?.[student.id];
                  const showGrade = canHaveGrade(lesson);
                  const gradeData = grades[lesson.id]?.[student.id];
                  const maxWorkNum = getMaxWorkNum(lesson.lesson_type);

                  return (
                    <TableCell key={lesson.id} className="text-center p-1">
                      <div className="flex flex-col items-center gap-0.5">
                        <AttendanceCell
                          status={status}
                          onStatusChange={(s) => onAttendanceChange(lesson.id, student.id, s)}
                        />
                        {showGrade && (
                          <GradeCell
                            gradeData={gradeData}
                            lesson={lesson}
                            maxWorkNum={maxWorkNum}
                            onGradeChange={(g, w) => onGradeChange(lesson.id, student.id, g, w)}
                          />
                        )}
                      </div>
                    </TableCell>
                  );
                })}
                {/* ИТОГО аттестации */}
                {attestationScores && (
                  <TableCell className={`text-center border-l ${isEven ? 'bg-background' : 'bg-muted/30'}`}>
                    {attestationScores[student.id] ? (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              className={`px-2 py-1 rounded-md text-sm font-semibold cursor-pointer transition-colors hover:opacity-80 ${getGradeColor(attestationScores[student.id].grade)}`}
                              onClick={() => onStudentAttestationClick?.(student, attestationScores[student.id])}
                            >
                              {attestationScores[student.id].total_score.toFixed(1)}
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="left" className="p-3 max-w-[200px]">
                            <div className="space-y-1.5 text-xs">
                              <div className="font-semibold border-b pb-1 mb-1">
                                {attestationScores[student.id].grade.toUpperCase()} ({attestationScores[student.id].total_score.toFixed(1)}/{attestationScores[student.id].max_points})
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Лабы:</span>
                                <span>{attestationScores[student.id].lab_score.toFixed(1)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Посещ.:</span>
                                <span>{attestationScores[student.id].attendance_score.toFixed(1)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Актив.:</span>
                                <span>{attestationScores[student.id].activity_score.toFixed(1)}</span>
                              </div>
                              {!attestationScores[student.id].is_passing && (
                                <div className="text-red-500 text-[10px] pt-1 border-t mt-1">
                                  Не хватает {(attestationScores[student.id].min_passing_points - attestationScores[student.id].total_score).toFixed(1)} б.
                                </div>
                              )}
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    ) : (
                      <span className="text-sm text-muted-foreground">—</span>
                    )}
                  </TableCell>
                )}
                <TableCell className={`sticky right-0 z-10 text-center font-semibold border-l ${isEven ? 'bg-background' : 'bg-muted/30'}`}>
                  {percentage !== null ? (
                    <span className={`text-sm ${percentage < 60 ? 'text-red-600' : percentage < 80 ? 'text-yellow-600' : 'text-green-600'}`}>
                      {percentage}%
                    </span>
                  ) : (
                    <span className="text-sm text-muted-foreground">—</span>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      
      {/* Add Activity Dialog */}
      {selectedStudentForActivity && attestationPeriod && (
        <AddActivityDialog
          open={activityDialogOpen}
          onOpenChange={setActivityDialogOpen}
          targetId={selectedStudentForActivity.id}
          targetName={selectedStudentForActivity.full_name}
          mode="student"
          onSuccess={() => {
            setSelectedStudentForActivity(null);
            onActivityAdded?.();
          }}
        />
      )}
    </div>
  );
}
