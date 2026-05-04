'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import type { AttestationSubjectOption, StudentLab } from '@/lib/api';
import { StudentAPI } from '@/lib/api';
import { getFilteredLabs, getLabsFilterCounts } from './labs-page-model';
import type { FilterStatus } from './types';

export function useStudentLabsPage() {
  const [subjectScopeResolved, setSubjectScopeResolved] = useState(false);
  const [subjectScopeError, setSubjectScopeError] = useState(false);
  const [subjectsLoading, setSubjectsLoading] = useState(true);
  const [labsLoading, setLabsLoading] = useState(false);
  const [subjects, setSubjects] = useState<AttestationSubjectOption[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);
  const [labs, setLabs] = useState<StudentLab[]>([]);
  const [filter, setFilter] = useState<FilterStatus>('all');
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const mustChooseSubject = subjects.length > 1 && !selectedSubjectId;
  const selectedSubject = selectedSubjectId ? subjects.find((subject) => subject.id === selectedSubjectId) ?? null : null;

  const loadLabs = useCallback(async (options?: { forceRefresh?: boolean }) => {
    if (!subjectScopeResolved || subjectScopeError) {
      setLabs([]);
      setLabsLoading(false);
      return;
    }
    if (subjects.length > 1 && !selectedSubjectId) {
      setLabs([]);
      setLabsLoading(false);
      return;
    }

    setLabsLoading(true);
    try {
      const data = await StudentAPI.getLabs({
        forceRefresh: options?.forceRefresh,
        subjectId: selectedSubjectId ?? undefined,
      });
      setLabs(data);
    } catch {
      toast.error('Ошибка загрузки лабораторных');
    } finally {
      setLabsLoading(false);
    }
  }, [selectedSubjectId, subjectScopeError, subjectScopeResolved, subjects.length]);

  useEffect(() => {
    let cancelled = false;

    async function loadSubjectContext() {
      setSubjectsLoading(true);
      try {
        const bootstrap = await StudentAPI.getDashboardBootstrap();
        const nextSubjects = await StudentAPI.getAttestationSubjects(bootstrap.overview.attestation_type);
        if (cancelled) return;

        setSubjects(nextSubjects);
        setSubjectScopeError(nextSubjects.length === 0);
        setSubjectScopeResolved(true);
        setSelectedSubjectId(nextSubjects.length === 1 ? nextSubjects[0].id : null);
        if (nextSubjects.length === 0) {
          toast.error('Не удалось определить предмет для лабораторных');
        }
      } catch {
        if (!cancelled) {
          toast.error('Ошибка загрузки предметов');
          setSubjects([]);
          setSubjectScopeError(true);
          setSubjectScopeResolved(true);
          setSelectedSubjectId(null);
        }
      } finally {
        if (!cancelled) setSubjectsLoading(false);
      }
    }

    void loadSubjectContext();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (subjectsLoading) return;
    void loadLabs();
  }, [loadLabs, subjectsLoading]);

  const selectSubject = (subjectId: string) => {
    setSelectedSubjectId(subjectId);
    setFilter('all');
    setLabs([]);
    setHoveredIndex(null);
    setActionLoading(null);
  };

  const handleMarkReady = async (labId: string) => {
    setActionLoading(labId);
    try {
      await StudentAPI.markLabReady(labId);
      toast.success('Вы в очереди! Подойдите к преподавателю с тетрадью.');
      await loadLabs({ forceRefresh: true });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Ошибка');
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancelReady = async (labId: string) => {
    setActionLoading(labId);
    try {
      await StudentAPI.cancelLabReady(labId);
      toast.success('Вы вышли из очереди');
      await loadLabs({ forceRefresh: true });
    } catch {
      toast.error('Ошибка');
    } finally {
      setActionLoading(null);
    }
  };

  const counts = useMemo(() => getLabsFilterCounts(labs), [labs]);
  const filteredLabs = useMemo(() => getFilteredLabs(labs, filter), [filter, labs]);
  const progress = labs.length > 0 ? Math.round((counts.accepted / labs.length) * 100) : 0;

  return {
    actionLoading,
    counts,
    filter,
    filteredLabs,
    hoveredIndex,
    labs,
    loading: subjectsLoading || labsLoading,
    mustChooseSubject,
    progress,
    selectedSubject,
    selectedSubjectId,
    subjects,
    subjectScopeError,
    handleCancelReady,
    handleMarkReady,
    selectSubject,
    setFilter,
    setHoveredIndex,
  };
}
