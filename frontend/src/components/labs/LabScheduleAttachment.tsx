'use client';

import { useEffect, useState } from 'react';
import { Calendar, Check, AlertTriangle, Loader2, ChevronDown, Ban } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
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
  attachment_blocked?: {
    blocking_lab_number: number;
    can_attach_from: string | null;
    message: string;
  };
}

interface Props {
  labId: string;
  labNumber: number;
}

export function LabScheduleAttachment({ labId, labNumber }: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
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
      await loadSlots(); // Перезагрузить для обновления блокировки
    } catch (error: unknown) {
      // Обработка ошибки блокировки
      const axiosError = error as { response?: { status?: number; data?: { detail?: { error?: string; message?: string } } } };
      if (axiosError.response?.status === 409 && axiosError.response?.data?.detail?.error === 'previous_lab_active') {
        toast.error(axiosError.response.data.detail.message || 'Предыдущая лаба ещё активна');
      } else {
        toast.error('Ошибка сохранения');
      }
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

  // Count total attached
  const attachedCount = selected.size;
  const totalSlots = data?.groups.reduce((sum, g) => sum + g.slots.length, 0) || 0;

  if (loading) {
    return (
      <Card>
        <div className="p-4 flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">Загрузка расписания...</span>
        </div>
      </Card>
    );
  }

  if (!data || data.groups.length === 0) {
    return (
      <Card>
        <div className="p-4 flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            Нет лабораторных занятий на ближайшие 2 недели
          </span>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <button className="w-full p-4 flex items-center justify-between hover:bg-muted/50 transition-colors rounded-t-lg">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium text-sm">Привязка к расписанию</span>
              <Badge variant="secondary" className="text-xs">
                {attachedCount} / {totalSlots}
              </Badge>
              {hasChanges && (
                <Badge variant="outline" className="text-xs text-orange-600 border-orange-300">
                  не сохранено
                </Badge>
              )}
            </div>
            <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0 pb-4">
            {/* Предупреждение о блокировке */}
            {data.attachment_blocked && (
              <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-start gap-3">
                <Ban className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-yellow-600">Привязка заблокирована</p>
                  <p className="text-muted-foreground mt-1">{data.attachment_blocked.message}</p>
                  {data.attachment_blocked.can_attach_from && (
                    <p className="text-muted-foreground mt-1">
                      Можно привязать после: <span className="font-medium">{new Date(data.attachment_blocked.can_attach_from).toLocaleDateString('ru-RU')}</span>
                    </p>
                  )}
                </div>
              </div>
            )}
            
            <Accordion type="multiple" defaultValue={data.groups.map(g => g.group_id)}>
              {data.groups.map(group => (
                <AccordionItem key={group.group_id} value={group.group_id}>
                  <AccordionTrigger className="hover:no-underline py-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{group.group_name}</span>
                      <Badge variant="secondary" className="text-xs">
                        {group.slots.filter(s => selected.has(s.lesson_id)).length} / {group.slots.length}
                      </Badge>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-1 pl-2">
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
            
            <div className="mt-4 flex justify-end">
              <Button 
                onClick={handleSave} 
                disabled={!hasChanges || saving || !!data.attachment_blocked}
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
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
