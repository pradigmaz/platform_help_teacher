'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { Loader2, Image as ImageIcon, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import api from '@/lib/api';
import type { Attachment } from './types';

interface ImageGalleryModalProps {
  isOpen: boolean;
  onClose: () => void;
  feedbackId: string;
  attachments: Attachment[];
  initialIndex?: number;
}

export function ImageGalleryModal({ 
  isOpen, 
  onClose, 
  feedbackId, 
  attachments, 
  initialIndex = 0 
}: ImageGalleryModalProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [urls, setUrls] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (isOpen) {
      setCurrentIndex(initialIndex);
    }
  }, [isOpen, initialIndex]);

  const loadUrl = async (attachment: Attachment) => {
    if (urls[attachment.id] || loading[attachment.id]) return;
    
    setLoading(prev => ({ ...prev, [attachment.id]: true }));
    try {
      const { data } = await api.get(`/feedback/${feedbackId}/attachments/${attachment.id}/url`);
      setUrls(prev => ({ ...prev, [attachment.id]: data.url }));
    } catch {
      toast.error('Не удалось загрузить изображение');
    } finally {
      setLoading(prev => ({ ...prev, [attachment.id]: false }));
    }
  };

  useEffect(() => {
    if (isOpen && attachments[currentIndex]) {
      loadUrl(attachments[currentIndex]);
    }
  }, [isOpen, currentIndex, feedbackId]);

  const goToPrevious = () => {
    setCurrentIndex(prev => prev > 0 ? prev - 1 : attachments.length - 1);
  };

  const goToNext = () => {
    setCurrentIndex(prev => prev < attachments.length - 1 ? prev + 1 : 0);
  };

  if (!attachments[currentIndex]) return null;

  const currentAttachment = attachments[currentIndex];
  const currentUrl = urls[currentAttachment.id];
  const isLoading = loading[currentAttachment.id];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] p-0">
        <DialogHeader className="p-6 pb-0">
          <DialogTitle className="flex items-center justify-between">
            <span>{currentAttachment.filename}</span>
            {attachments.length > 1 && (
              <span className="text-sm text-muted-foreground">
                {currentIndex + 1} из {attachments.length}
              </span>
            )}
          </DialogTitle>
        </DialogHeader>
        
        <div className="relative flex-1 min-h-0 p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-96">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : currentUrl ? (
            <div className="relative">
              <div className="relative max-w-full max-h-[70vh] mx-auto" style={{ width: '100%', height: '70vh' }}>
                <Image 
                  src={currentUrl} 
                  alt={currentAttachment.filename}
                  fill
                  className="rounded-lg object-contain"
                />
              </div>
              
              {attachments.length > 1 && (
                <>
                  <Button
                    variant="outline"
                    size="icon"
                    className="absolute left-4 top-1/2 -translate-y-1/2 bg-background/80 backdrop-blur-sm"
                    onClick={goToPrevious}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="absolute right-4 top-1/2 -translate-y-1/2 bg-background/80 backdrop-blur-sm"
                    onClick={goToNext}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-96 text-muted-foreground">
              <div className="text-center">
                <ImageIcon className="h-12 w-12 mx-auto mb-2" />
                <p>Не удалось загрузить изображение</p>
              </div>
            </div>
          )}
        </div>

        {attachments.length > 1 && (
          <div className="p-6 pt-0">
            <div className="flex gap-2 overflow-x-auto">
              {attachments.map((att, index) => (
                <button
                  key={att.id}
                  onClick={() => setCurrentIndex(index)}
                  className={`flex-shrink-0 w-16 h-16 rounded border-2 overflow-hidden relative ${
                    index === currentIndex ? 'border-primary' : 'border-muted'
                  }`}
                >
                  {urls[att.id] ? (
                    <Image src={urls[att.id]} alt={att.filename} fill className="object-cover" />
                  ) : (
                    <div className="w-full h-full bg-muted flex items-center justify-center">
                      <ImageIcon className="h-4 w-4 text-muted-foreground" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}