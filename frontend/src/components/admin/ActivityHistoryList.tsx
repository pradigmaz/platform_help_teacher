'use client';

import { Calendar, History, Loader2, Trash2, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { BlurFade } from '@/components/ui/blur-fade';
import { cn } from '@/lib/utils';
import type { GroupedActivityEntry } from './activityManagementModel';
import { getActivityInitials } from './activityManagementModel';

interface ActivityHistoryListProps {
  entries: GroupedActivityEntry[];
  loading: boolean;
  onDelete: (id: string) => void;
}

export function ActivityHistoryList({
  entries,
  loading,
  onDelete,
}: ActivityHistoryListProps) {
  return (
    <div>
      <h4 className="text-sm font-medium mb-4 flex items-center gap-2">
        <History className="w-4 h-4 text-muted-foreground" />
        История начислений
        {entries.length > 0 && (
          <Badge variant="secondary" className="ml-auto">
            {entries.length} записей
          </Badge>
        )}
      </h4>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
        </div>
      ) : entries.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <History className="w-12 h-12 mx-auto mb-3 opacity-20" />
          <p className="text-sm">Нет записей для этой аттестации</p>
        </div>
      ) : (
        <ScrollArea className="h-[320px] pr-4">
          <div className="space-y-3">
            {entries.map((entry, index) => (
              <BlurFade key={entry.key} delay={0.02 + index * 0.015}>
                <div
                  className={cn(
                    'group relative flex items-start gap-3 p-4 rounded-xl border transition-all',
                    'hover:bg-muted/50 hover:border-purple-500/20 hover:shadow-sm'
                  )}
                >
                  <div
                    className={cn(
                      'h-10 w-10 shrink-0 rounded-full flex items-center justify-center text-xs font-medium',
                      entry.first.points > 0 ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'
                    )}
                  >
                    {entry.isGroup ? <Users className="w-4 h-4" /> : getActivityInitials(entry.first.student_name || '??')}
                  </div>

                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        variant={entry.first.points > 0 ? 'default' : 'destructive'}
                        className={cn('font-mono text-xs px-2', entry.first.points > 0 && 'bg-green-500 hover:bg-green-600')}
                      >
                        {entry.first.points > 0 ? '+' : ''}
                        {entry.first.points}
                      </Badge>

                      {entry.isGroup ? (
                        <span className="text-sm font-medium text-blue-500">
                          {entry.uniqueGroups.join(', ')}
                          <span className="text-muted-foreground font-normal ml-1">
                            ({entry.activities.length} чел.)
                          </span>
                        </span>
                      ) : (
                        <>
                          <span className="text-sm font-medium">{entry.first.student_name}</span>
                          {entry.first.group_name && (
                            <Badge variant="outline" className="text-xs font-normal">
                              {entry.first.group_name}
                            </Badge>
                          )}
                        </>
                      )}
                    </div>

                    <p className="text-sm text-muted-foreground line-clamp-1">{entry.first.description}</p>

                    <div className="flex items-center gap-1 text-xs text-muted-foreground/70">
                      <Calendar className="w-3 h-3" />
                      {new Date(entry.first.created_at).toLocaleDateString('ru-RU', {
                        day: 'numeric',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>

                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    onClick={() => onDelete(entry.first.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </BlurFade>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
