'use client';

import { useEffect, useState, useRef } from 'react';
import { Bug, Lightbulb, Clock, CheckCircle, XCircle, Loader2, Image as ImageIcon, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { BlurFade } from '@/components/ui/blur-fade';
import api from '@/lib/api';

type FeedbackType = 'bug' | 'suggestion';
type FeedbackStatus = 'new' | 'in_progress' | 'resolved' | 'closed';

interface Attachment {
  id: string;
  filename: string;
  content_type: string;
  size: number;
}

interface Feedback {
  id: string;
  type: FeedbackType;
  title: string;
  description: string;
  status: FeedbackStatus;
  user_id: string;
  user_name: string | null;
  group_name: string | null;
  admin_response: string | null;
  attachments: Attachment[];
  created_at: string;
  resolved_at: string | null;
}

const statusLabels: Record<FeedbackStatus, { label: string; icon: React.ReactNode; color: string }> = {
  new: { label: 'Новое', icon: <Clock className="h-3 w-3" />, color: 'bg-blue-500' },
  in_progress: { label: 'В работе', icon: <Loader2 className="h-3 w-3" />, color: 'bg-yellow-500' },
  resolved: { label: 'Решено', icon: <CheckCircle className="h-3 w-3" />, color: 'bg-green-500' },
  closed: { label: 'Закрыто', icon: <XCircle className="h-3 w-3" />, color: 'bg-gray-500' },
};

function AttachmentPreview({ feedbackId, attachment }: { feedbackId: string; attachment: Attachment }) {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadUrl = async () => {
    if (url || loading) return;
    setLoading(true);
    try {
      const { data } = await api.get(`/feedback/${feedbackId}/attachments/${attachment.id}/url`);
      setUrl(data.url);
    } catch {
      toast.error('Не удалось загрузить изображение');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="relative group cursor-pointer border rounded overflow-hidden bg-muted"
      onClick={loadUrl}
    >
      {url ? (
        <a href={url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}>
          <img src={url} alt={attachment.filename} className="h-24 w-24 object-cover" />
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <ExternalLink className="h-5 w-5 text-white" />
          </div>
        </a>
      ) : (
        <div className="h-24 w-24 flex items-center justify-center">
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          ) : (
            <ImageIcon className="h-8 w-8 text-muted-foreground" />
          )}
        </div>
      )}
    </div>
  );
}

export default function FeedbackPage() {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FeedbackStatus | 'all'>('all');
  const [responses, setResponses] = useState<Record<string, string>>({});
  const abortRef = useRef<AbortController | null>(null);

  const fetchFeedbacks = async () => {
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
  };

  useEffect(() => {
    fetchFeedbacks();
    return () => abortRef.current?.abort();
  }, [filter]);

  const updateStatus = async (id: string, status: FeedbackStatus) => {
    try {
      const response = responses[id];
      await api.patch(`/feedback/${id}`, { status, admin_response: response || undefined });
      toast.success('Статус обновлён');
      fetchFeedbacks();
    } catch {
      toast.error('Ошибка обновления');
    }
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
        <div className="space-y-4">
          {feedbacks.map((fb, i) => (
            <BlurFade key={fb.id} delay={0.1 + i * 0.05}>
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-2">
                      {fb.type === 'bug' ? (
                        <Bug className="h-5 w-5 text-red-500" />
                      ) : (
                        <Lightbulb className="h-5 w-5 text-yellow-500" />
                      )}
                      <CardTitle className="text-lg">{fb.title}</CardTitle>
                    </div>
                    <Badge className={`${statusLabels[fb.status].color} text-white gap-1`}>
                      {statusLabels[fb.status].icon}
                      {statusLabels[fb.status].label}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {fb.user_name || 'Неизвестный пользователь'}
                    {fb.group_name && <span className="ml-1">• {fb.group_name}</span>}
                    {' • '}
                    {new Date(fb.created_at).toLocaleDateString('ru', { 
                      day: 'numeric', 
                      month: 'short',
                      year: 'numeric'
                    })}
                    {' в '}
                    {new Date(fb.created_at).toLocaleTimeString('ru', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="whitespace-pre-wrap">{fb.description}</p>
                  
                  {/* Attachments */}
                  {fb.attachments.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {fb.attachments.map(att => (
                        <AttachmentPreview key={att.id} feedbackId={fb.id} attachment={att} />
                      ))}
                    </div>
                  )}
                  
                  {fb.status !== 'closed' && (
                    <div className="space-y-2 pt-2 border-t">
                      <Textarea
                        placeholder="Ответ (опционально)"
                        value={responses[fb.id] || fb.admin_response || ''}
                        onChange={(e) => setResponses({ ...responses, [fb.id]: e.target.value })}
                        rows={2}
                      />
                      <div className="flex gap-2">
                        {fb.status === 'new' && (
                          <Button size="sm" variant="outline" onClick={() => updateStatus(fb.id, 'in_progress')}>
                            Взять в работу
                          </Button>
                        )}
                        {fb.status !== 'resolved' && (
                          <Button size="sm" variant="default" onClick={() => updateStatus(fb.id, 'resolved')}>
                            Решено
                          </Button>
                        )}
                        <Button size="sm" variant="ghost" onClick={() => updateStatus(fb.id, 'closed')}>
                          Закрыть
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </BlurFade>
          ))}
        </div>
      )}
    </div>
  );
}
