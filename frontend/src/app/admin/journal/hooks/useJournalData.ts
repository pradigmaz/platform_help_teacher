'use client';

import { useEffect } from 'react';
import type { Lesson } from '../lib/journal-constants';
import { useJournalFilters, type AttestationPeriod, type SemesterInfo } from './useJournalFilters';
import { useJournalLessons } from './useJournalLessons';
import { useJournalStats } from './useJournalStats';
import { useJournalAttendance } from './useJournalAttendance';
import { useJournalGrades } from './useJournalGrades';

// Re-export types for backward compatibility
export type { AttestationPeriod, SemesterInfo };

interface UseJournalDataProps {
  lessonIdParam: string | null;
}

export function useJournalData({ lessonIdParam }: UseJournalDataProps) {
  // Filters
  const filters = useJournalFilters();
  
  // Stats (needs to be created first for refetch callback)
  const statsHook = useJournalStats({
    selectedGroupId: filters.selectedGroupId,
    selectedSubjectId: filters.selectedSubjectId,
    weekStart: filters.weekStart,
    weekEnd: filters.weekEnd,
    lessonsCount: 0, // Will be updated
  });

  // Attendance
  const attendanceHook = useJournalAttendance({
    onStatsRefetch: statsHook.refetchStats,
  });

  // Grades
  const gradesHook = useJournalGrades({
    attendance: attendanceHook.attendance,
    updateAttendance: attendanceHook.updateAttendance,
    onStatsRefetch: statsHook.refetchStats,
  });

  // Lessons
  const lessonsHook = useJournalLessons({
    selectedGroupId: filters.selectedGroupId,
    selectedSubjectId: filters.selectedSubjectId,
    selectedLessonType: filters.selectedLessonType,
    weekStart: filters.weekStart,
    weekEnd: filters.weekEnd,
    attestationPeriod: filters.attestationPeriod,
    selectedSemester: filters.selectedSemester,
    getSemesterStart: filters.getSemesterStart,
    lessonIdParam,
    setSelectedGroupId: filters.setSelectedGroupId,
    setSelectedSubjectId: filters.setSelectedSubjectId,
    setCurrentWeek: filters.setCurrentWeek,
  });

  // Load attendance, grades, stats when lessons change
  useEffect(() => {
    if (lessonsHook.lessons.length > 0 && filters.selectedGroupId) {
      const lessonIds = lessonsHook.lessons.map((l: Lesson) => l.id);
      
      Promise.all([
        attendanceHook.loadAttendance(filters.selectedGroupId, lessonIds),
        gradesHook.loadGrades(lessonIds),
        statsHook.loadStats(
          filters.selectedGroupId,
          lessonsHook.startDate,
          lessonsHook.endDate,
          filters.selectedSubjectId
        ),
      ]);
      
      // Load attestation scores if period selected
      if (filters.attestationPeriod !== 'all') {
        gradesHook.loadAttestationScores(filters.selectedGroupId, filters.attestationPeriod);
      }
    } else {
      attendanceHook.setAttendance({});
      gradesHook.setGrades({});
      statsHook.setStats(null);
    }
  }, [lessonsHook.lessons, filters.selectedGroupId, filters.attestationPeriod]);

  return {
    // Filters
    selectedGroupId: filters.selectedGroupId,
    setSelectedGroupId: filters.setSelectedGroupId,
    selectedSubjectId: filters.selectedSubjectId,
    setSelectedSubjectId: filters.setSelectedSubjectId,
    selectedLessonType: filters.selectedLessonType,
    setSelectedLessonType: filters.setSelectedLessonType,
    currentWeek: filters.currentWeek,
    setCurrentWeek: filters.setCurrentWeek,
    attestationPeriod: filters.attestationPeriod,
    setAttestationPeriod: filters.setAttestationPeriod,
    selectedSemester: filters.selectedSemester,
    setSelectedSemester: filters.setSelectedSemester,
    
    // Lessons data
    groups: lessonsHook.groups,
    subjects: lessonsHook.subjects,
    lessons: lessonsHook.lessons,
    students: lessonsHook.students,
    isLoading: lessonsHook.isLoading,
    
    // Attendance
    attendance: attendanceHook.attendance,
    updateAttendance: attendanceHook.updateAttendance,
    
    // Grades
    grades: gradesHook.grades,
    attestationScores: gradesHook.attestationScores,
    updateGrade: gradesHook.updateGrade,
    
    // Stats
    stats: statsHook.stats,
    
    // Saving state
    isSaving: attendanceHook.isSaving || gradesHook.isSaving,
  };
}
