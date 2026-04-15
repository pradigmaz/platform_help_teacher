'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import type { SubjectBrief, LectureListResponse } from '@/lib/lectures-api';
import LecturesAPI from '@/lib/lectures-api';
import api from '@/lib/api';
import {
  type AdminLectureSubject as Subject,
  loadAdminLecturesList,
  primeAdminLectureDetail,
} from '@/lib/admin-lectures-cache';
import { downloadMarkdownFile, lexicalToMarkdown } from '@/lib/utils/lexical-markdown';

export function useLectures() {
  const [lectures, setLectures] = useState<LectureListResponse[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);

  const fetchData = useCallback(async (force = false) => {
    try {
      const data = await loadAdminLecturesList(async () => {
        const [lecturesData, subjectsData] = await Promise.all([
          LecturesAPI.list(),
          api.get<Subject[]>('/admin/subjects/').then((response) => response.data),
        ]);

        return { lectures: lecturesData, subjects: subjectsData };
      }, force);

      setLectures(data.lectures);
      setSubjects(data.subjects);
    } catch {
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const lecturesBySubject = useMemo(() => {
    const grouped: Record<string, { subject: SubjectBrief | null; lectures: LectureListResponse[] }> = {};

    grouped.none = { subject: null, lectures: [] };

    subjects.forEach((subject) => {
      grouped[subject.id] = {
        subject: { id: subject.id, name: subject.name, code: subject.code },
        lectures: [],
      };
    });

    lectures.forEach((lecture) => {
      const key = lecture.subject_id || 'none';
      if (grouped[key]) {
        grouped[key].lectures.push(lecture);
        return;
      }

      grouped.none.lectures.push(lecture);
    });

    return grouped;
  }, [lectures, subjects]);

  const filteredLectures = useMemo(() => {
    if (!selectedSubjectId) return lectures;
    if (selectedSubjectId === 'none') return lectures.filter((lecture) => !lecture.subject_id);
    return lectures.filter((lecture) => lecture.subject_id === selectedSubjectId);
  }, [lectures, selectedSubjectId]);

  const handleDelete = useCallback(async (id: string, title: string) => {
    if (!confirm(`Удалить лекцию "${title}"?`)) {
      return;
    }

    try {
      await LecturesAPI.delete(id);
      toast.success('Лекция удалена');
      await fetchData(true);
    } catch {
      toast.error('Ошибка удаления');
    }
  }, [fetchData]);

  const handlePublish = useCallback(async (id: string) => {
    try {
      const result = await LecturesAPI.publish(id);
      toast.success('Лекция опубликована');
      await navigator.clipboard.writeText(`${window.location.origin}/lectures/view/${result.public_code}`);
      toast.info('Ссылка скопирована');
      await fetchData(true);
    } catch {
      toast.error('Ошибка публикации');
    }
  }, [fetchData]);

  const handleUnpublish = useCallback(async (id: string) => {
    try {
      await LecturesAPI.unpublish(id);
      toast.success('Публикация отменена');
      await fetchData(true);
    } catch {
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
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
      toast.success('PDF скачан');
    } catch {
      toast.error('Ошибка экспорта PDF');
    }
  }, []);

  const handleExportMarkdown = useCallback(async (id: string, title: string) => {
    try {
      const lecture = await LecturesAPI.get(id);
      primeAdminLectureDetail(lecture);
      const markdown = lexicalToMarkdown(lecture.content);
      downloadMarkdownFile(title, markdown || `# ${title}`);
      toast.success('Markdown скачан');
    } catch {
      toast.error('Ошибка экспорта Markdown');
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
    handleExportMarkdown,
  };
}
