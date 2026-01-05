'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  FlaskConical, 
  CheckCircle2, 
  Clock, 
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { LabSubmissionPublic } from '@/lib/api';

interface LabSubmissionsProps {
  submissions: LabSubmissionPublic[];
  completed: number;
  total: number;
}

export function LabSubmissions({ submissions, completed, total }: LabSubmissionsProps) {
  const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;
  
  // Sort by lab number
  const sortedSubmissions = [...submissions].sort((a, b) => a.lab_number - b.lab_number);

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5 text-muted-foreground" />
            <CardTitle>Лабораторные работы</CardTitle>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-sm">
              <span className="text-muted-foreground">Сдано: </span>
              <span className="font-medium">{completed} из {total}</span>
            </div>
            <Badge variant="outline" className={cn(
              completionRate >= 80 ? 'bg-green-500/10 text-green-600' :
              completionRate >= 50 ? 'bg-yellow-500/10 text-yellow-600' :
              'bg-red-500/10 text-red-600'
            )}>
              {completionRate}%
            </Badge>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mt-2">
          <Progress value={completionRate} className="h-2" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sortedSubmissions.map((lab) => (
            <LabRow key={lab.lab_id} lab={lab} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function LabRow({ lab }: { lab: LabSubmissionPublic }) {
  const isSubmitted = lab.is_submitted;
  const isLate = lab.is_late;
  const hasGrade = lab.grade !== undefined && lab.grade !== null;
  
  const getStatusConfig = () => {
    if (!isSubmitted) {
      return {
        icon: XCircle,
        color: 'text-red-500',
        bgColor: 'bg-red-500/10',
        label: 'Не сдано',
        badgeClass: 'bg-red-500/10 text-red-600 border-red-200',
      };
    }
    if (isLate) {
      return {
        icon: AlertTriangle,
        color: 'text-yellow-500',
        bgColor: 'bg-yellow-500/10',
        label: 'Сдано с опозданием',
        badgeClass: 'bg-yellow-500/10 text-yellow-600 border-yellow-200',
      };
    }
    return {
      icon: CheckCircle2,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      label: 'Сдано',
      badgeClass: 'bg-green-500/10 text-green-600 border-green-200',
    };
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const formattedDate = lab.submitted_at ? formatDate(lab.submitted_at) : null;

  return (
    <div className={cn(
      "flex items-center gap-3 p-3 rounded-lg transition-colors",
      isSubmitted ? "bg-muted/50 hover:bg-muted" : "bg-red-500/5 hover:bg-red-500/10"
    )}>
      {/* Status Icon */}
      <div className={cn("p-2 rounded-lg flex-shrink-0", config.bgColor)}>
        <Icon className={cn("h-4 w-4", config.color)} />
      </div>

      {/* Lab Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">
            Лаб. {lab.lab_number}
          </span>
          <span className="text-sm text-muted-foreground truncate">
            {lab.lab_name}
          </span>
        </div>
        {formattedDate && (
          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
            <Clock className="h-3 w-3" />
            {formattedDate}
          </p>
        )}
      </div>

      {/* Grade */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {hasGrade ? (
          <div className="text-right">
            <div className="flex items-baseline gap-1">
              <span className="text-lg font-bold">{lab.grade}</span>
              <span className="text-xs text-muted-foreground">/ {lab.max_grade}</span>
            </div>
          </div>
        ) : (
          <Badge variant="outline" className={config.badgeClass}>
            {config.label}
          </Badge>
        )}
      </div>
    </div>
  );
}

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}
