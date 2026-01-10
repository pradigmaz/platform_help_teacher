'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { InputGroup, InputGroupAddon, InputGroupInput, InputGroupText } from '@/components/ui/input-group';
import { IconTarget } from '@tabler/icons-react';
import { LabData, UpdateFieldFn } from './types';

interface HeaderTabProps {
  data: LabData;
  updateField: UpdateFieldFn;
}

export function HeaderTab({ data, updateField }: HeaderTabProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2">
            <IconTarget className="h-5 w-5 text-primary" />
            Основная информация
          </CardTitle>
          <CardDescription>Номер, название и цель лабораторной работы</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex gap-4">
            <div className="w-24 shrink-0">
              <Label htmlFor="lab-number">Номер</Label>
              <InputGroup className="mt-1.5">
                <InputGroupAddon>
                  <InputGroupText>№</InputGroupText>
                </InputGroupAddon>
                <InputGroupInput
                  id="lab-number"
                  type="number"
                  min={1}
                  value={data.number}
                  onChange={(e) => updateField('number', Number(e.target.value))}
                />
              </InputGroup>
            </div>
            <div className="flex-1">
              <Label htmlFor="lab-title">Название (тема) *</Label>
              <Input
                id="lab-title"
                className="mt-1.5"
                value={data.title}
                onChange={(e) => updateField('title', e.target.value)}
                placeholder="Unit-тестирование в C#"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="lab-goal">Цель работы</Label>
            <Textarea
              id="lab-goal"
              className="mt-1.5"
              value={data.goal || ''}
              onChange={(e) => updateField('goal', e.target.value)}
              placeholder="Научиться писать unit-тесты..."
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base">Дополнительные настройки</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label htmlFor="lab-formatting">Что записать в тетрадь</Label>
            <Textarea
              id="lab-formatting"
              className="mt-1.5"
              value={data.formatting_guide || ''}
              onChange={(e) => updateField('formatting_guide', e.target.value)}
              placeholder="1. Тема и цель работы..."
              rows={5}
            />
          </div>
          <Separator />
          <div className="flex gap-6">
            <div className="flex-1">
              <Label htmlFor="lab-deadline">Дедлайн</Label>
              <Input
                id="lab-deadline"
                className="mt-1.5"
                type="datetime-local"
                value={data.deadline || ''}
                onChange={(e) => updateField('deadline', e.target.value)}
              />
            </div>
            <div className="flex items-center gap-3 pt-6">
              <Switch
                id="is_sequential"
                checked={data.is_sequential}
                onCheckedChange={(checked) => updateField('is_sequential', checked)}
              />
              <Label htmlFor="is_sequential" className="cursor-pointer">
                Последовательная сдача
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
