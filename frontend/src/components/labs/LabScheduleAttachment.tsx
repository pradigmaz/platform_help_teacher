'use client';

import { useEffect, useState } from 'react';
import { Calendar, Check, AlertTriangle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import api from '@/lib/api';

interface ScheduleSlot {
  lesson_id: string;
  date: string;
  lesson_number: number;
  subgroup: number | null;
  current_work_number: number | null;
  is_attached: boolean;
}

interface GroupSlots {
  group_id: string;
  group_name: string;
  slots: ScheduleSlot[];
}

interface ScheduleSlotsResponse {
  lab_number: number;
  groups: GroupSlots[];
}

interface Props {
  labId: string;
  labNumber: number;
}

export function LabScheduleAttachment({ labId, labNumber }: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState<ScheduleSlotsResponse | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [initialSelected, setInitialSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadSlots();
  }, [labId]);

  const loadSlots = async () => {
    try {
      const { data: resp } = await api.get<ScheduleSlotsResponse>(
        `/admin/labs/${labId}/schedule-slots`
      );
      setData(resp);
      
      // Set initially selected (already attached)
      const attached = new Set<string>();
      resp.groups.forEach(g => {
        g.slots.forEach(s => {
          if (s.is_attached) attached.add(s.lesson_id);
        });
      });
      setSelected(attached);
      setInitialSelected(attached);
    } catch {
      toast.error('Не удалось загрузить расписание');
    } finally {
      setLoading(false);
    }
  };

  const toggleSlot = (lessonId: string, slot: ScheduleSlot) => {
    // Can't select if occupied by another lab
    if (slot.current_work_number && slot.current_work_number !== labNumber) {
      return;
    }
    
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(lessonId)) {
        next.delete(lessonId);
      } else {
        next.add(lessonId);
      }
      return next;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Find what to attach and detach
      const toAttach = [...selected].filter(id => !initialSelected.has(id));
      const toDetach = [...initialSelected].filter(id => !selected.has(id));
      
      if (toAttach.length > 0) {
        await api.post(`/admin/labs/${labId}/attach`, { lesson_ids: toAttach });
      }
      if (toDetach.length > 0) {
        await api.post(`/admin/labs/${labId}/detach`, { lesson_ids: toDetach });
      }
      
      toast.success('Привязки обновлены');
      setInitialSelected(new Set(selected));
    } catch {
      toast.error('Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const hasChanges = 
    [...selected].some(id => !initialSelected.has(id)) ||
    [...initialSelected].some(id => !selected.has(id));

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric', month: 'short' });
  };

  const formatSubgroup = (sg: number | null) => {
    if (sg === null) return 'вся группа';
    return `${sg} п/г`;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 flex justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (!data || data.groups.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Привязка к расписанию
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            Нет лабораторных занятий в расписании на ближайшие 2 недели
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Привязка к расписанию
          </CardTitle>
          <Button 
            onClick={handleSave} 
            disabled={!hasChanges || saving}
            size="sm"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Check className="h-4 w-4 mr-2" />
            )}
            Применить
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Accordion type="multiple" defaultValue={data.groups.map(g => g.group_id)}>
          {data.groups.map(group => (
            <AccordionItem key={group.group_id} value={group.group_id}>
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{group.group_name}</span>
                  <Badge variant="secondary" className="text-xs">
                    {group.slots.filter(s => selected.has(s.lesson_id)).length} / {group.slots.length}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-2 pl-2">
                  {group.slots.map(slot => {
                    const isOccupied = slot.current_work_number && slot.current_work_number !== labNumber;
                    const isChecked = selected.has(slot.lesson_id);
                    
                    return (
                      <label
                        key={slot.lesson_id}
                        className={`flex items-center gap-3 p-2 rounded-md cursor-pointer transition-colors ${
                          isOccupied 
                            ? 'opacity-50 cursor-not-allowed bg-muted' 
                            : 'hover:bg-muted/50'
                        }`}
                      >
                        <Checkbox
                          checked={isChecked}
                          onCheckedChange={() => toggleSlot(slot.lesson_id, slot)}
                          disabled={!!isOccupied}
                        />
                        <span className="text-sm">
                          {formatSubgroup(slot.subgroup)} — {formatDate(slot.date)}, пара {slot.lesson_number}
                        </span>
                        {isOccupied && (
                          <Badge variant="outline" className="text-xs text-yellow-600 border-yellow-300">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            ЛР №{slot.current_work_number}
                          </Badge>
                        )}
                      </label>
                    );
                  })}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </CardContent>
    </Card>
  );
}
