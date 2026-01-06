'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Users, BookOpen } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useJournalData, AttestationPeriod, SemesterInfo } from './hooks/useJournalData';
import { LessonSheet } from '@/components/schedule';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  JournalFilters,
  JournalWeekNav,
  JournalStats,
  JournalTable,
  JournalLegend,
} from './components';
import type { Lesson } from './lib/journal-constants';

export default function JournalPage() {
  const searchParams = useSearchParams();
  const lessonIdParam = searchParams.get('lesson_id');
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null);

  const {
    groups,
    subjects,
    selectedGroupId,
    setSelectedGroupId,
    selectedSubjectId,
    setSelectedSubjectId,
    selectedLessonType,
    setSelectedLessonType,
    currentWeek,
    setCurrentWeek,
    attestationPeriod,
    setAttestationPeriod,
    selectedSemester,
    setSelectedSemester,
    lessons,
    students,
    attendance,
    grades,
    attestationScores,
    stats,
    isLoading,
    updateAttendance,
    updateGrade,
  } = useJournalData({ lessonIdParam });

  // Generate semester options (current year and previous)
  const now = new Date();
  const currentAcademicYear = now.getMonth() >= 8 ? now.getFullYear() : now.getFullYear() - 1;
  const semesterOptions: SemesterInfo[] = [
    { academicYear: currentAcademicYear, semester: 1 },
    { academicYear: currentAcademicYear, semester: 2 },
    { academicYear: currentAcademicYear - 1, semester: 1 },
    { academicYear: currentAcademicYear - 1, semester: 2 },
  ];

  const formatSemester = (sem: SemesterInfo) => 
    `${sem.semester} сем. ${sem.academicYear}-${sem.academicYear + 1}`;

  const semesterKey = (sem: SemesterInfo) => `${sem.academicYear}-${sem.semester}`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Журнал</h1>
          <p className="text-muted-foreground mt-1">Посещаемость и оценки</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <JournalFilters
          groups={groups}
          subjects={subjects}
          selectedGroupId={selectedGroupId}
          selectedSubjectId={selectedSubjectId}
          selectedLessonType={selectedLessonType}
          onGroupChange={setSelectedGroupId}
          onSubjectChange={setSelectedSubjectId}
          onLessonTypeChange={setSelectedLessonType}
        />
        
        {/* Semester Selector */}
        <Select 
          value={semesterKey(selectedSemester)} 
          onValueChange={(v) => {
            const [year, sem] = v.split('-').map(Number);
            setSelectedSemester({ academicYear: year, semester: sem as 1 | 2 });
          }}
        >
          <SelectTrigger className="w-[180px] h-9">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {semesterOptions.map((sem) => (
              <SelectItem key={semesterKey(sem)} value={semesterKey(sem)}>
                {formatSemester(sem)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        {/* Attestation Period Selector */}
        <Tabs value={attestationPeriod} onValueChange={(v) => setAttestationPeriod(v as AttestationPeriod)}>
          <TabsList className="h-9">
            <TabsTrigger value="all" className="text-xs px-3">Неделя</TabsTrigger>
            <TabsTrigger value="first" className="text-xs px-3">1-я аттест.</TabsTrigger>
            <TabsTrigger value="second" className="text-xs px-3">2-я аттест.</TabsTrigger>
          </TabsList>
        </Tabs>
        
        {/* Week navigation only when viewing by week */}
        {attestationPeriod === 'all' && (
          <JournalWeekNav
            currentWeek={currentWeek}
            onWeekChange={setCurrentWeek}
          />
        )}
      </div>

      {/* Stats */}
      {stats && <JournalStats stats={stats} />}

      {/* Main content */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : !selectedGroupId ? (
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground">
            <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Выберите группу</p>
          </CardContent>
        </Card>
      ) : lessons.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground">
            <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Нет занятий за выбранный период</p>
          </CardContent>
        </Card>
      ) : (
        <Card className="border-0 shadow-sm">
          <CardContent className="p-0">
            <JournalTable
              lessons={lessons}
              students={students}
              attendance={attendance}
              grades={grades}
              attestationScores={attestationPeriod !== 'all' ? attestationScores : undefined}
              attestationPeriod={attestationPeriod !== 'all' ? attestationPeriod : undefined}
              onAttendanceChange={updateAttendance}
              onGradeChange={updateGrade}
              onLessonClick={setSelectedLesson}
              onActivityAdded={() => {
                // Trigger re-fetch by toggling attestation period
                const current = attestationPeriod;
                setAttestationPeriod('all');
                setTimeout(() => setAttestationPeriod(current), 100);
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Legend */}
      <JournalLegend />

      {/* Lesson Sheet */}
      <LessonSheet
        lesson={selectedLesson ? {
          ...selectedLesson,
          group_id: selectedGroupId,
          group_name: groups.find(g => g.id === selectedGroupId)?.name
        } : null}
        isOpen={!!selectedLesson}
        onClose={() => setSelectedLesson(null)}
        onSave={() => {
          // Refresh data after save
          setSelectedLesson(null);
        }}
      />
    </div>
  );
}
