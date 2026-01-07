'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Settings } from 'lucide-react';

interface LabSettings {
  labs_count: number;
  grading_scale: '5' | '10' | '100';
  default_max_grade: number;
}

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  settings: LabSettings;
  setSettings: (settings: LabSettings) => void;
  onSave: () => void;
}

export function SettingsDialog({ open, onOpenChange, settings, setSettings, onSave }: SettingsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Настройки лабораторных
          </DialogTitle>
          <DialogDescription>
            Количество лабораторных для отслеживания прогресса.
            Шкала оценок настраивается в разделе «Аттестация».
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="labs_count">Количество лабораторных</Label>
            <Input 
              id="labs_count" 
              type="number" 
              min={1} 
              max={50} 
              value={settings.labs_count} 
              onChange={(e) => setSettings({ ...settings, labs_count: parseInt(e.target.value) || 10 })} 
            />
            <p className="text-xs text-muted-foreground">Сколько лабораторных работ в семестре</p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>
          <Button onClick={onSave}>Сохранить</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
