'use client';

import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface ComponentToggleProps {
  title: string;
  icon: LucideIcon;
  enabled: boolean;
  weight: number;
  onToggle: (enabled: boolean) => void;
  onWeightChange: (weight: number) => void;
  children?: React.ReactNode;
  color?: string;
}

export function ComponentToggle({
  title,
  icon: Icon,
  enabled,
  weight,
  onToggle,
  onWeightChange,
  children,
  color = '#8b5cf6'
}: ComponentToggleProps) {
  return (
    <Card className={cn('transition-all duration-200', !enabled && 'opacity-60')}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div 
              className="p-2 rounded-lg"
              style={{ backgroundColor: `${color}20`, color }}
            >
              <Icon className="w-5 h-5" />
            </div>
            <span className="font-medium">{title}</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min={0}
                max={100}
                value={weight}
                onChange={(e) => onWeightChange(parseFloat(e.target.value) || 0)}
                disabled={!enabled}
                className="w-20 h-8 text-center"
              />
              <span className="text-sm text-muted-foreground">%</span>
            </div>
            <Switch checked={enabled} onCheckedChange={onToggle} />
          </div>
        </div>
      </CardHeader>
      {enabled && children && (
        <CardContent className="pt-0 border-t">
          <div className="pt-4">
            {children}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
