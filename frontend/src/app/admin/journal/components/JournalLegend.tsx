'use client';

import { FileQuestion } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { STATUS_INFO } from '../lib/journal-constants';

export function JournalLegend() {
  return (
    <div className="flex justify-end">
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="ghost" size="sm" className="text-muted-foreground">
            <FileQuestion className="w-4 h-4 mr-1" />
            Легенда
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto" align="end">
          <div className="space-y-2 text-sm">
            <p className="font-medium mb-2">Статусы посещаемости:</p>
            {Object.entries(STATUS_INFO).map(([key, info]) => (
              <div key={key} className="flex items-center gap-2">
                <info.icon className={`w-4 h-4 ${info.color}`} />
                <span>{info.label}</span>
              </div>
            ))}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
