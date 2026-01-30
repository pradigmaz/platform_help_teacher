import React from 'react';
import { Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';

export type FeedbackType = 'bug' | 'suggestion';
export type FeedbackStatus = 'new' | 'in_progress' | 'resolved' | 'closed';

export interface Attachment {
  id: string;
  filename: string;
  content_type: string;
  size: number;
}

export interface Feedback {
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

export const statusLabels: Record<FeedbackStatus, { label: string; icon: React.ReactNode; color: string }> = {
  new: { label: 'Новое', icon: React.createElement(Clock, { className: "h-3 w-3" }), color: 'bg-blue-500' },
  in_progress: { label: 'В работе', icon: React.createElement(Loader2, { className: "h-3 w-3" }), color: 'bg-yellow-500' },
  resolved: { label: 'Решено', icon: React.createElement(CheckCircle, { className: "h-3 w-3" }), color: 'bg-green-500' },
  closed: { label: 'Закрыто', icon: React.createElement(XCircle, { className: "h-3 w-3" }), color: 'bg-gray-500' },
};