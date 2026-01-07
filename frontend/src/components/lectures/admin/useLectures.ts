'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { toast } from 'sonner';
import LecturesAPI, { LectureListResponse, SubjectBrief } from '@/lib/lectures-api';
import api from '@/lib/api';

interface Subject {
  id: string;
  name: string;
  code: string | null;
  is_active: boolean;
}

export function useLectures() {
  const [lectures, setLectures] = useState<LectureListResponse[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [lecturesData, subjectsData] = await Promise.all([
        LecturesAPI.list(),
        api.get<Subject[]>('/admin/subjects/').then(r => r.data)
      ]);
      setLectures(lecturesData);
      setSubjects(subjectsData);
    } catch (error) {
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Группировка лекций по предметам
  const lecturesBySubject = useMemo(() => {
    const grouped: Record<string, { subject: SubjectBrief | null; lectures: LectureListResponse[] }> = {};
    
    grouped['none'] = { subject: null, lectures: [] };
    
    subjects.forEach(s => {
      grouped[s.id] = { subject: { id: s.id, name: s.name, code: s.code }, lectures: [] };
    });
    
    lectures.forEach(lecture => {
      const key = lecture.subject_id || 'none';
      if (grouped[key]) {
        grouped[key].lectures.push(lecture);
      } else {
        grouped['none'].lectures.push(lecture);
      }
    });
    
    return grouped;
  }, [lectures, subjects]);

  // Фильтрованные лекции
  const filteredLectures = useMemo(() => {
    if (!selectedSubjectId) return lectures;
    if (selectedSubjectId === 'none') return lectures.filter(l => !l.subject_id);
    return lectures.filter(l => l.subject_id === selectedSubjectId);
  }, [lectures, selectedSubjectId]);

  const handleDelete = useCallback(async (id: string, title: string) => {
    if (!confirm(`Удалить лекцию "${title}"?`)) return;
    try {
      await LecturesAPI.delete(id);
      toast.success('Лекция удалена');
      fetchData();
    } catch (error) {
      toast.error('Ошибка удаления');
    }
  }, [fetchData]);

  const handlePublish = useCallback(async (id: string) => {
    try {
      const result = await LecturesAPI.publish(id);
      toast.success('Лекция опубликована');
      await navigator.clipboard.writeText(`${window.location.origin}/lectures/view/${result.public_code}`);
      toast.info('Ссылка скопирована');
      fetchData();
    } catch (error) {
      toast.error('Ошибка публикации');
    }
  }, [fetchData]);

  const handleUnpublish = useCallback(async (id: string) => {
    try {
      await LecturesAPI.unpublish(id);
      toast.success('Публикация отменена');
      fetchData();
    } catch (error) {
      toast.error('Ошибка');
    }
  }, [fetchData]);

  const handleCopyLink = useCallback(async (code: string) => {
    await navigator.clipboard.writeText(`${window.location.origin}/lectures/view/${code}`);
    toast.success('Ссылка скопирована');
  }, []);

  const handleExportPdf = useCallback(async (id: string, title: string) => {
    try {
      toast.info('Генерация PDF...');
      const blob = await LecturesAPI.exportPdf(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('PDF скачан');
    } catch (error) {
      toast.error('Ошибка экспорта PDF');
    }
  }, []);

  return {
    lectures,
    subjects,
    loading,
    selectedSubjectId,
    setSelectedSubjectId,
    lecturesBySubject,
    filteredLectures,
    fetchData,
    handleDelete,
    handlePublish,
    handleUnpublish,
    handleCopyLink,
    handleExportPdf,
  };
}
