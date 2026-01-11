'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Plus, FlaskConical, Settings, Users } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';
import { LabQueueAPI } from '@/lib/api/lab-queue';
import type { LabQueue, SubmissionDetail } from '@/lib/api/types/lab-queue';

import { BlurFade } from '@/components/ui/blur-fade';
import { Sparkles } from '@/components/ui/sparkles';

import {
  LabsTable,
  StatsCards,
  SettingsDialog,
  QueueDialog,
  GradeDialog,
  RejectDialog,
} from './components';

interface Lab {
  id: string;
  title: string;
  description: string | null;
  max_grade: number;
  deadline: string | null;
  created_at: string;
}

interface LabSettings {
  labs_count: number;
  grading_scale: '5' | '10' | '100';
  default_max_grade: number;
  is_configured: boolean;
}

export default function AdminLabsPage() {
  // Labs state
  const [labs, setLabs] = useState<Lab[]>([]);
  const [loading, setLoading] = useState(true);

  // Settings state
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [labSettings, setLabSettings] = useState<LabSettings>({
    labs_count: 10, grading_scale: '10', default_max_grade: 10, is_configured: true,
  });

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

  useEffect(() => {
    fetchLabs();
    fetchSettings();
  }, []);

  const fetchLabs = async () => {
    try {
      const response = await api.get('/admin/labs');
      setLabs(response.data);
    } catch { toast.error('Ошибка загрузки лабораторных работ'); }
    finally { setLoading(false); }
  };

  const fetchSettings = async () => {
    try {
      const response = await api.get('/admin/lab-settings');
      setLabSettings(response.data);
      // Если настройки не сконфигурированы — открываем диалог
      if (!response.data.is_configured) {
        setSettingsDialogOpen(true);
      }
    } catch { console.error('Ошибка загрузки настроек'); }
  };

  const fetchQueue = async () => {
    setQueueLoading(true);
    try {
      const data = await LabQueueAPI.getQueue();
      setQueue(data);
    } catch { toast.error('Ошибка загрузки очереди'); }
    finally { setQueueLoading(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить лабораторную работу?')) return;
    try {
      await api.delete(`/admin/labs/${id}`);
      toast.success('Удалено');
      fetchLabs();
    } catch { toast.error('Ошибка удаления'); }
  };

  const handleSaveSettings = async () => {
    try {
      await api.patch('/admin/lab-settings', labSettings);
      toast.success('Настройки сохранены');
      setLabSettings({ ...labSettings, is_configured: true });
      setSettingsDialogOpen(false);
    } catch { toast.error('Ошибка сохранения настроек'); }
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

  const completedLabs = labs.length;
  const progressPercent = labSettings.labs_count > 0 
    ? Math.round((completedLabs / labSettings.labs_count) * 100) : 0;

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
          <Button variant="outline" onClick={openQueueDialog}>
            <Users className="mr-2 h-4 w-4" /> Очередь на сдачу
          </Button>
          <Button variant="outline" onClick={() => setSettingsDialogOpen(true)}>
            <Settings className="mr-2 h-4 w-4" /> Настройки
          </Button>
          <Button asChild className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90">
            <Link href="/admin/labs/new"><Plus className="mr-2 h-4 w-4" /> Создать</Link>
          </Button>
        </div>

        <StatsCards completedLabs={completedLabs} plannedLabs={labSettings.labs_count} progressPercent={progressPercent} />

        <LabsTable labs={labs} onDelete={handleDelete} />
      </div>

      {/* Dialogs */}
      <SettingsDialog 
        open={settingsDialogOpen} 
        onOpenChange={(open) => {
          // Не позволяем закрыть диалог если настройки не сконфигурированы
          if (!open && !labSettings.is_configured) return;
          setSettingsDialogOpen(open);
        }} 
        settings={labSettings} 
        setSettings={setLabSettings} 
        onSave={handleSaveSettings}
        isInitialSetup={!labSettings.is_configured}
      />
      <QueueDialog
        open={queueDialogOpen} onOpenChange={setQueueDialogOpen} queue={queue} loading={queueLoading}
        onRefresh={fetchQueue} selectedSubmission={selectedSubmission} onSelectSubmission={handleSelectSubmission}
        onAccept={() => setGradeDialogOpen(true)} onReject={() => setRejectDialogOpen(true)}
      />
      <GradeDialog open={gradeDialogOpen} onOpenChange={setGradeDialogOpen} submission={selectedSubmission} form={gradeForm} setForm={setGradeForm} onAccept={handleAccept} />
      <RejectDialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen} submission={selectedSubmission} comment={rejectComment} setComment={setRejectComment} onReject={handleReject} />
    </div>
  );
}
