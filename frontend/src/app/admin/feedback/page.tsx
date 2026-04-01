'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { BlurFade } from '@/components/ui/blur-fade';
import { FeedbackCard } from '@/components/admin/feedback/FeedbackCard';
import { ImageGalleryModal } from '@/components/admin/feedback/ImageGalleryModal';
import { type Feedback, type FeedbackStatus, type Attachment } from '@/components/admin/feedback/types';
import api from '@/lib/api';

export default function FeedbackPage() {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FeedbackStatus | 'all'>('all');
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [galleryModal, setGalleryModal] = useState<{
    isOpen: boolean;
    feedbackId: string;
    attachments: Attachment[];
    initialIndex: number;
  }>({
    isOpen: false,
    feedbackId: '',
    attachments: [],
    initialIndex: 0,
  });
  const abortRef = useRef<AbortController | null>(null);

  const fetchFeedbacks = useCallback(async () => {
    // Cancel previous request
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      const params = filter !== 'all' ? { status: filter } : {};
      const { data } = await api.get<Feedback[]>('/feedback', { 
        params,
        signal: abortRef.current.signal,
      });
      setFeedbacks(data);
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== 'CanceledError') {
        toast.error('Не удалось загрузить обращения');
      }
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void fetchFeedbacks();
    return () => abortRef.current?.abort();
  }, [fetchFeedbacks]);

  const updateStatus = useCallback(async (id: string, status: FeedbackStatus) => {
    try {
      const response = responses[id];
      await api.patch(`/feedback/${id}`, { status, admin_response: response || undefined });
      toast.success('Статус обновлён');
      await fetchFeedbacks();
    } catch {
      toast.error('Ошибка обновления');
    }
  }, [fetchFeedbacks, responses]);

  const openGallery = (feedbackId: string, attachments: Attachment[], initialIndex: number) => {
    setGalleryModal({
      isOpen: true,
      feedbackId,
      attachments,
      initialIndex,
    });
  };

  const closeGallery = () => {
    setGalleryModal(prev => ({ ...prev, isOpen: false }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <BlurFade delay={0.1}>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Обратная связь</h1>
          <Select value={filter} onValueChange={(v) => setFilter(v as FeedbackStatus | 'all')}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все</SelectItem>
              <SelectItem value="new">Новые</SelectItem>
              <SelectItem value="in_progress">В работе</SelectItem>
              <SelectItem value="resolved">Решённые</SelectItem>
              <SelectItem value="closed">Закрытые</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </BlurFade>

      {feedbacks.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            Нет обращений
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {feedbacks.map((fb, i) => (
            <FeedbackCard
              key={fb.id}
              feedback={fb}
              index={i}
              responses={responses}
              onResponseChange={(id, value) => setResponses({ ...responses, [id]: value })}
              onStatusUpdate={updateStatus}
              onOpenGallery={openGallery}
            />
          ))}
        </div>
      )}

      <ImageGalleryModal
        isOpen={galleryModal.isOpen}
        onClose={closeGallery}
        feedbackId={galleryModal.feedbackId}
        attachments={galleryModal.attachments}
        initialIndex={galleryModal.initialIndex}
      />
    </div>
  );
}
