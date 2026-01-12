'use client';

import { MessageSquarePlus } from 'lucide-react';
import { FeedbackDialog } from './FeedbackDialog';
import { Button } from '@/components/ui/button';

/**
 * Floating Action Button for feedback.
 * Fixed position in bottom-right corner.
 */
export function FeedbackFab() {
  return (
    <div className="fixed bottom-6 right-6 z-50">
      <FeedbackDialog
        trigger={
          <Button
            size="lg"
            className="h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-shadow bg-primary hover:bg-primary/90"
          >
            <MessageSquarePlus className="h-6 w-6" />
          </Button>
        }
      />
    </div>
  );
}
