'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { BookOpen, GraduationCap } from 'lucide-react';

interface SelfWorksConfig {
  self_works_enabled: boolean;
  self_works_weight: number;
  self_works_grade_5_points: number;
  self_works_grade_4_points: number;
  self_works_grade_3_points: number;
  self_works_grade_2_points: number;
}

interface ColloquiumConfig {
  colloquium_enabled: boolean;
  colloquium_weight: number;
  colloquium_grade_5_points: number;
  colloquium_grade_4_points: number;
  colloquium_grade_3_points: number;
  colloquium_grade_2_points: number;
}

interface Props {
  selfWorks: SelfWorksConfig;
  colloquium: ColloquiumConfig;
  onSelfWorksChange: <K extends keyof SelfWorksConfig>(key: K, value: SelfWorksConfig[K]) => void;
  onColloquiumChange: <K extends keyof ColloquiumConfig>(key: K, value: ColloquiumConfig[K]) => void;
}

export function OptionalComponentSettings({ 
  selfWorks, colloquium,
  onSelfWorksChange, onColloquiumChange 
}: Props) {
  return (
    <div className="space-y-4">
      {/* Самостоятельные работы */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <BookOpen className="w-5 h-5 text-orange-500" />
              Самостоятельные работы
            </CardTitle>
            <Switch checked={selfWorks.self_works_enabled}
              onCheckedChange={v => onSelfWorksChange('self_works_enabled', v)} />
          </div>
        </CardHeader>
        {selfWorks.self_works_enabled && (
          <CardContent className="space-y-4">
            <div>
              <Label>Вес (%)</Label>
              <Input type="number" value={selfWorks.self_works_weight}
                onChange={e => onSelfWorksChange('self_works_weight', Number(e.target.value))} />
            </div>
            <div className="grid grid-cols-4 gap-2">
              <div><Label className="text-xs">За 5</Label>
                <Input type="number" step="0.1" value={selfWorks.self_works_grade_5_points}
                  onChange={e => onSelfWorksChange('self_works_grade_5_points', Number(e.target.value))} /></div>
              <div><Label className="text-xs">За 4</Label>
                <Input type="number" step="0.1" value={selfWorks.self_works_grade_4_points}
                  onChange={e => onSelfWorksChange('self_works_grade_4_points', Number(e.target.value))} /></div>
              <div><Label className="text-xs">За 3</Label>
                <Input type="number" step="0.1" value={selfWorks.self_works_grade_3_points}
                  onChange={e => onSelfWorksChange('self_works_grade_3_points', Number(e.target.value))} /></div>
              <div><Label className="text-xs">За 2</Label>
                <Input type="number" step="0.1" value={selfWorks.self_works_grade_2_points}
                  onChange={e => onSelfWorksChange('self_works_grade_2_points', Number(e.target.value))} /></div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Коллоквиум */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <GraduationCap className="w-5 h-5 text-indigo-500" />
              Коллоквиум
            </CardTitle>
            <Switch checked={colloquium.colloquium_enabled}
              onCheckedChange={v => onColloquiumChange('colloquium_enabled', v)} />
          </div>
        </CardHeader>
        {colloquium.colloquium_enabled && (
          <CardContent className="space-y-4">
            <div>
              <Label>Вес (%)</Label>
              <Input type="number" value={colloquium.colloquium_weight}
                onChange={e => onColloquiumChange('colloquium_weight', Number(e.target.value))} />
            </div>
            <div className="grid grid-cols-4 gap-2">
              <div><Label className="text-xs">За 5</Label>
                <Input type="number" step="0.1" value={colloquium.colloquium_grade_5_points}
                  onChange={e => onColloquiumChange('colloquium_grade_5_points', Number(e.target.value))} /></div>
              <div><Label className="text-xs">За 4</Label>
                <Input type="number" step="0.1" value={colloquium.colloquium_grade_4_points}
                  onChange={e => onColloquiumChange('colloquium_grade_4_points', Number(e.target.value))} /></div>
              <div><Label className="text-xs">За 3</Label>
                <Input type="number" step="0.1" value={colloquium.colloquium_grade_3_points}
                  onChange={e => onColloquiumChange('colloquium_grade_3_points', Number(e.target.value))} /></div>
              <div><Label className="text-xs">За 2</Label>
                <Input type="number" step="0.1" value={colloquium.colloquium_grade_2_points}
                  onChange={e => onColloquiumChange('colloquium_grade_2_points', Number(e.target.value))} /></div>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
