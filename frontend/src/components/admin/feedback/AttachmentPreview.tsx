'use client';

import { useEffect, useState } from 'react';
import { Loader2, Image as ImageIcon } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';
import type { Attachment } from './types';

interface AttachmentPreviewProps {
  feedbackId: string;
  attachment: Attachment;
  onClick: () => void;
}

export function AttachmentPreview({ feedbackId, attachment, onClick }: AttachmentPreviewProps) {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUrl = async () => {
      try {
        const { data } = await api.get(`/feedback/${feedbackId}/attachments/${attachment.id}/url`);
        setUrl(data.url);
      } catch {
        toast.error('Не удалось загрузить изображение');
      } finally {
        setLoading(false);
      }
    };
    loadUrl();
  }, [feedbackId, attachment.id]);

  return (
    <div 
      className="relative group cursor-pointer border rounded-lg overflow-hidden bg-muted hover:bg-muted/80 transition-colors"
      onClick={onClick}
    >
      {url ? (
        <div className="relative">
          <img src={url} alt={attachment.filename} className="h-24 w-24 object-cover" />
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
            <div className="opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 rounded-full p-2">
              <ImageIcon className="h-4 w-4 text-white" />
            </div>
          </div>
        </div>
      ) : (
        <div className="h-24 w-24 flex items-center justify-center">
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          ) : (
            <div className="text-center">
              <ImageIcon className="h-6 w-6 text-muted-foreground mx-auto mb-1" />
              <span className="text-xs text-muted-foreground">Ошибка</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}