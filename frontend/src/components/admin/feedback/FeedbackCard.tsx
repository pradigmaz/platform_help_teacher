import { Bug, Lightbulb, Clock, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { BlurFade } from '@/components/ui/blur-fade';
import { AttachmentPreview } from './AttachmentPreview';
import { statusLabels, type Feedback, type FeedbackStatus, type Attachment } from './types';

interface FeedbackCardProps {
  feedback: Feedback;
  index: number;
  responses: Record<string, string>;
  onResponseChange: (id: string, value: string) => void;
  onStatusUpdate: (id: string, status: FeedbackStatus) => void;
  onOpenGallery: (feedbackId: string, attachments: Attachment[], initialIndex: number) => void;
}

export function FeedbackCard({
  feedback: fb,
  index,
  responses,
  onResponseChange,
  onStatusUpdate,
  onOpenGallery,
}: FeedbackCardProps) {
  return (
    <BlurFade key={fb.id} delay={0.1 + index * 0.05}>
      <Card className="shadow-sm hover:shadow-md transition-shadow">
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              {fb.type === 'bug' ? (
                <div className="p-2 bg-red-50 rounded-lg">
                  <Bug className="h-5 w-5 text-red-600" />
                </div>
              ) : (
                <div className="p-2 bg-yellow-50 rounded-lg">
                  <Lightbulb className="h-5 w-5 text-yellow-600" />
                </div>
              )}
              <div>
                <CardTitle className="text-lg leading-tight">{fb.title}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {fb.user_name || 'Неизвестный пользователь'}
                  {fb.group_name && <span className="ml-1">• {fb.group_name}</span>}
                </p>
              </div>
            </div>
            <div className="flex flex-col items-end gap-2">
              <Badge className={`${statusLabels[fb.status].color} text-white gap-1.5 px-3 py-1`}>
                {statusLabels[fb.status].icon}
                {statusLabels[fb.status].label}
              </Badge>
              <time className="text-xs text-muted-foreground">
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
              </time>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="prose prose-sm max-w-none">
            <p className="whitespace-pre-wrap text-foreground leading-relaxed">{fb.description}</p>
          </div>
          
          {/* Attachments */}
          {fb.attachments.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-muted-foreground">
                Вложения ({fb.attachments.length})
              </h4>
              <div className="flex flex-wrap gap-3">
                {fb.attachments.map((att, index) => (
                  <AttachmentPreview 
                    key={att.id} 
                    feedbackId={fb.id} 
                    attachment={att}
                    onClick={() => onOpenGallery(fb.id, fb.attachments, index)}
                  />
                ))}
              </div>
            </div>
          )}
          
          {fb.status !== 'closed' && (
            <div className="space-y-4 pt-4 border-t bg-muted/30 -mx-6 px-6 py-4 rounded-b-lg">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Ответ администратора</label>
                <Textarea
                  placeholder="Введите ответ (опционально)..."
                  value={responses[fb.id] || fb.admin_response || ''}
                  onChange={(e) => onResponseChange(fb.id, e.target.value)}
                  rows={3}
                  className="resize-none"
                />
              </div>
              <div className="flex gap-2 flex-wrap">
                {fb.status === 'new' && (
                  <Button size="sm" variant="outline" onClick={() => onStatusUpdate(fb.id, 'in_progress')}>
                    <Clock className="h-4 w-4 mr-1" />
                    Взять в работу
                  </Button>
                )}
                {fb.status !== 'resolved' && (
                  <Button size="sm" variant="default" onClick={() => onStatusUpdate(fb.id, 'resolved')}>
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Решено
                  </Button>
                )}
                <Button size="sm" variant="ghost" onClick={() => onStatusUpdate(fb.id, 'closed')}>
                  <XCircle className="h-4 w-4 mr-1" />
                  Закрыть
                </Button>
              </div>
            </div>
          )}

          {fb.status === 'closed' && fb.admin_response && (
            <div className="pt-4 border-t">
              <div className="bg-muted/50 rounded-lg p-4">
                <h4 className="text-sm font-medium mb-2 text-muted-foreground">Ответ администратора:</h4>
                <p className="text-sm whitespace-pre-wrap">{fb.admin_response}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </BlurFade>
  );
}