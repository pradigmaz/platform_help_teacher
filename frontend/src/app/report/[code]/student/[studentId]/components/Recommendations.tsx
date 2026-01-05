'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Lightbulb, 
  AlertTriangle,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface RecommendationsProps {
  recommendations: string[];
  isPassing?: boolean;
}

export function Recommendations({ recommendations, isPassing }: RecommendationsProps) {
  if (recommendations.length === 0) return null;

  const isAtRisk = !isPassing;

  return (
    <Card className={cn(
      "border-l-4",
      isAtRisk ? "border-l-amber-500" : "border-l-blue-500"
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isAtRisk ? (
              <AlertTriangle className="h-5 w-5 text-amber-500" />
            ) : (
              <Lightbulb className="h-5 w-5 text-blue-500" />
            )}
            <CardTitle className="text-lg">
              {isAtRisk ? 'Требуется внимание' : 'Рекомендации'}
            </CardTitle>
          </div>
          {isAtRisk && (
            <Badge variant="outline" className="bg-amber-500/10 text-amber-600 border-amber-200">
              Риск незачёта
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {recommendations.map((rec, index) => (
            <li key={index} className="flex items-start gap-3">
              <div className={cn(
                "p-1 rounded-full mt-0.5 flex-shrink-0",
                isAtRisk ? "bg-amber-500/10" : "bg-blue-500/10"
              )}>
                <ArrowRight className={cn(
                  "h-3 w-3",
                  isAtRisk ? "text-amber-500" : "text-blue-500"
                )} />
              </div>
              <span className="text-sm">{rec}</span>
            </li>
          ))}
        </ul>

        {isAtRisk && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-muted-foreground flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              Выполнение рекомендаций поможет получить зачёт
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
