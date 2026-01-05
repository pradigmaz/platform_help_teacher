'use client';

import { cn } from '@/lib/utils';
import type { TOCItem } from './types';

interface Props {
  items: TOCItem[];
  activeId: string;
  onItemClick: (id: string) => void;
}

export function LecturePublicTOC({ items, activeId, onItemClick }: Props) {
  if (items.length === 0) return null;

  return (
    <nav className="space-y-1">
      <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-4 px-3">
        Содержание
      </h4>
      
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-0 top-2 bottom-2 w-0.5 bg-border rounded-full" />
        
        {items.map((item, index) => (
          <button
            key={`${item.id}-${index}`}
            onClick={() => onItemClick(item.id)}
            className={cn(
              "block w-full text-left px-4 py-2 text-sm rounded-lg transition-all duration-200 border-l-2 -ml-[1px]",
              item.level === 2 && "pl-6",
              item.level === 3 && "pl-8",
              activeId === item.id
                ? "border-primary font-medium text-primary bg-primary/5"
                : "border-transparent text-muted-foreground hover:text-foreground hover:bg-accent"
            )}
          >
            {item.text}
          </button>
        ))}
      </div>
    </nav>
  );
}
