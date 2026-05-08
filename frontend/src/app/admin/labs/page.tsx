'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { FlaskConical, Settings, Users, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { LabsAPI, SubjectsAPI, type GroupSubjectOffering } from '@/lib/api';
import { LabQueueAPI } from '@/lib/api/lab-queue';
import type { LabQueue, SubmissionDetail } from '@/lib/api/types/lab-queue';
import type { Lab } from '@/lib/api/types/labs';

import { BlurFade } from '@/components/ui/blur-fade';
import { Sparkles } from '@/components/ui/sparkles';

import {
  LabsTable,
  StatsCards,
  SubjectPolicyDialog,
  QueueDialog,
  GradeDialog,
  RejectDialog,
  DeadlineExtensionsDialog,
} from './components';
import { getAdminLabOfferingOptions, getSelectedOfferingOption } from './components/subjectOptions';

export default function AdminLabsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Labs state
  const [labs, setLabs] = useState<Lab[]>([]);
  const [offerings, setOfferings] = useState<GroupSubjectOffering[]>([]);
  const [selectedOfferingId, setSelectedOfferingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [policyDialogOpen, setPolicyDialogOpen] = useState(false);

  // Queue state
  const [queueDialogOpen, setQueueDialogOpen] = useState(false);
  const [queue, setQueue] = useState<LabQueue[]>([]);
  const [queueLoading, setQueueLoading] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState<SubmissionDetail | null>(null);

  // Grade/Reject state
  const [gradeDialogOpen, setGradeDialogOpen] = useState(false);
  const [gradeForm, setGradeForm] = useState({ grade: 5, comment: '' });
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectComment, setRejectComment] = useState('');

  // Extensions state
  const [extensionsDialogOpen, setExtensionsDialogOpen] = useState(false);

  const offeringOptions = useMemo(() => getAdminLabOfferingOptions(offerings), [offerings]);
  const selectedOffering = getSelectedOfferingOption(offeringOptions, selectedOfferingId);
  const selectedSubjectId = selectedOffering?.subjectId ?? null;

  const prefetchCreateLabRoute = useCallback(() => {
    const href = selectedSubjectId
      ? `/admin/labs/new?subject_id=${selectedSubjectId}${selectedOfferingId ? `&offering_id=${selectedOfferingId}` : ''}`
      : '/admin/labs/new';
    router.prefetch(href);
    void import('@/app/admin/labs/new/page');
  }, [router, selectedOfferingId, selectedSubjectId]);

  const fetchLabs = useCallback(async (subjectId: string) => {
    try {
      setLabs(await LabsAPI.adminList(subjectId));
    } catch { toast.error('Ошибка загрузки лабораторных работ'); }
  }, []);

  const fetchOfferings = useCallback(async () => {
    setLoading(true);
    try {
      const nextOfferings = await SubjectsAPI.listOfferings();
      const nextOptions = getAdminLabOfferingOptions(nextOfferings);
      const requestedOfferingId = searchParams.get('offering_id');
      const requestedSubjectId = searchParams.get('subject_id');
      const nextOfferingId =
        nextOptions.find((offering) => offering.id === requestedOfferingId)?.id ??
        nextOptions.find((offering) => offering.subjectId === requestedSubjectId)?.id ??
        nextOptions[0]?.id ??
        null;
      setOfferings(nextOfferings);
      setSelectedOfferingId(nextOfferingId);
      if (!nextOfferingId) {
        setLabs([]);
      }
    } catch {
      toast.error('Ошибка загрузки предметов');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchOfferings();
  }, [fetchOfferings]);

  useEffect(() => {
    if (!selectedSubjectId) return;
    fetchLabs(selectedSubjectId);
  }, [fetchLabs, selectedOfferingId, selectedSubjectId]);

  useEffect(() => {
    if (loading) {
      return;
    }

    prefetchCreateLabRoute();

    const timeoutId = window.setTimeout(prefetchCreateLabRoute, 300);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [loading, prefetchCreateLabRoute]);

  const fetchQueue = async () => {
    if (!selectedSubjectId) {
      toast.error('Выберите предмет');
      return;
    }
    setQueueLoading(true);
    try {
      const data = await LabQueueAPI.getQueue(selectedSubjectId);
      setQueue(data);
    } catch { toast.error('Ошибка загрузки очереди'); }
    finally { setQueueLoading(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить лабораторную работу?')) return;
    try {
      await LabsAPI.adminDelete(id);
      toast.success('Удалено');
      if (selectedSubjectId) await fetchLabs(selectedSubjectId);
    } catch { toast.error('Ошибка удаления'); }
  };

  const handleSelectSubmission = async (submissionId: string) => {
    try {
      const detail = await LabQueueAPI.getSubmissionDetail(submissionId);
      setSelectedSubmission(detail);
      setGradeForm({ grade: 5, comment: '' });
    } catch { toast.error('Ошибка загрузки данных сдачи'); }
  };

  const handleAccept = async () => {
    if (!selectedSubmission) return;
    try {
      await LabQueueAPI.acceptSubmission(selectedSubmission.submission_id, gradeForm);
      toast.success(`Работа принята с оценкой ${gradeForm.grade}`);
      setGradeDialogOpen(false);
      setSelectedSubmission(null);
      fetchQueue();
    } catch { toast.error('Ошибка принятия работы'); }
  };

  const handleReject = async () => {
    if (!selectedSubmission || !rejectComment.trim()) return;
    try {
      await LabQueueAPI.rejectSubmission(selectedSubmission.submission_id, { comment: rejectComment });
      toast.success('Работа отклонена');
      setRejectDialogOpen(false);
      setRejectComment('');
      setSelectedSubmission(null);
      fetchQueue();
    } catch { toast.error('Ошибка отклонения работы'); }
  };

  const openQueueDialog = () => {
    setQueueDialogOpen(true);
    fetchQueue();
  };

  const createdLabs = labs.length;
  const publishedLabs = labs.filter((lab) => lab.is_published).length;

  const handleOfferingChange = useCallback((offeringId: string) => {
    setSelectedOfferingId(offeringId);
    setLabs([]);
  }, []);

  const openCreateLab = () => {
    if (!selectedSubjectId) {
      toast.error('Выберите предмет');
      return;
    }
    router.push(`/admin/labs/new?subject_id=${selectedSubjectId}${selectedOfferingId ? `&offering_id=${selectedOfferingId}` : ''}`);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="h-10 w-64 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="h-32 bg-muted animate-pulse rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <BlurFade delay={0.1}>
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <Sparkles color="#8b5cf6">
                <FlaskConical className="h-8 w-8 text-primary" />
              </Sparkles>
              Лабораторные работы
            </h1>
            <p className="text-muted-foreground mt-1">Управление лабораторными и настройками аттестации</p>
          </div>
        </div>
      </BlurFade>

      <div className="space-y-6 mt-6">
        {/* Actions */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setExtensionsDialogOpen(true)}>
            <Clock className="mr-2 h-4 w-4" /> Продления
          </Button>
          <Button variant="outline" onClick={openQueueDialog}>
            <Users className="mr-2 h-4 w-4" /> Очередь на сдачу
          </Button>
          <Button variant="outline" onClick={() => setPolicyDialogOpen(true)}>
            <Settings className="mr-2 h-4 w-4" /> Настройки по предметам
          </Button>
        </div>

        <StatsCards createdLabs={createdLabs} publishedLabs={publishedLabs} selectedOfferingLabel={selectedOffering?.label ?? ''} />

        <LabsTable
          labs={labs}
          offerings={offeringOptions}
          selectedOfferingId={selectedOfferingId}
          onOfferingChange={handleOfferingChange}
          onCreate={openCreateLab}
          onDelete={handleDelete}
        />
      </div>

      {/* Dialogs */}
      <SubjectPolicyDialog
        open={policyDialogOpen}
        onOpenChange={setPolicyDialogOpen}
        offerings={offeringOptions}
        selectedOfferingId={selectedOfferingId}
        onOfferingChange={handleOfferingChange}
      />
      <QueueDialog
        open={queueDialogOpen} onOpenChange={setQueueDialogOpen} queue={queue} loading={queueLoading}
        onRefresh={fetchQueue} selectedSubmission={selectedSubmission} onSelectSubmission={handleSelectSubmission}
        onAccept={() => setGradeDialogOpen(true)} onReject={() => setRejectDialogOpen(true)}
      />
      <GradeDialog open={gradeDialogOpen} onOpenChange={setGradeDialogOpen} submission={selectedSubmission} form={gradeForm} setForm={setGradeForm} onAccept={handleAccept} />
      <RejectDialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen} submission={selectedSubmission} comment={rejectComment} setComment={setRejectComment} onReject={handleReject} />
      <DeadlineExtensionsDialog open={extensionsDialogOpen} onOpenChange={setExtensionsDialogOpen} labs={labs} />
    </div>
  );
}
