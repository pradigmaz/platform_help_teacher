'use client';

import { useState } from 'react';
import { Copy, Check, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/sonner';

interface ReportLinkCopyProps {
  code: string;
}

export function ReportLinkCopy({ code }: ReportLinkCopyProps) {
  const [copied, setCopied] = useState(false);

  const getFullUrl = () => {
    if (typeof window !== 'undefined') {
      return `${window.location.origin}/report/${code}`;
    }
    return `/report/${code}`;
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(getFullUrl());
      setCopied(true);
      toast.success('Ссылка скопирована');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Не удалось скопировать');
    }
  };

  const handleOpen = () => {
    window.open(getFullUrl(), '_blank');
  };

  return (
    <div className="flex items-center gap-2">
      <code className="bg-muted px-2 py-1 rounded font-mono text-sm">{code}</code>
      <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={handleCopy}>
        {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
      </Button>
      <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={handleOpen}>
        <ExternalLink className="w-3.5 h-3.5" />
      </Button>
    </div>
  );
}
