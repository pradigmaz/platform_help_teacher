'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from '@/components/ui/sonner';
import { ReportsAPI, ReportType } from '@/lib/api';
import { Loader2 } from 'lucide-react';

interface CreateReportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groupId: string;
  onSuccess: () => void;
}

export function CreateReportDialog({ open, onOpenChange, groupId, onSuccess }: CreateReportDialogProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [reportType, setReportType] = useState<ReportType>('full');
  const [expiresInDays, setExpiresInDays] = useState<string>('none');
  const [pinCode, setPinCode] = useState('');
  const [showNames, setShowNames] = useState(true);
  const [showGrades, setShowGrades] = useState(true);
  const [showAttendance, setShowAttendance] = useState(true);
  const [showNotes, setShowNotes] = useState(true);
  const [showRating, setShowRating] = useState(true);

  const resetForm = () => {
    setReportType('full');
    setExpiresInDays('none');
    setPinCode('');
    setShowNames(true);
    setShowGrades(true);
    setShowAttendance(true);
    setShowNotes(true);
    setShowRating(true);
  };

  const handleSubmit = async () => {
    if (pinCode && (pinCode.length < 4 || pinCode.length > 6 || !/^\d+$/.test(pinCode))) {
      toast.error('PIN должен содержать 4-6 цифр');
      return;
    }

    setIsLoading(true);
    try {
      await ReportsAPI.create({
        group_id: groupId,
        report_type: reportType,
        expires_in_days: expiresInDays !== 'none' ? parseInt(expiresInDays) : null,
        pin_code: pinCode || null,
        show_names: showNames,
        show_grades: showGrades,
        show_attendance: showAttendance,
        show_notes: showNotes,
        show_rating: showRating,
      });
      toast.success('Отчёт создан');
      resetForm();
      onSuccess();
    } catch (e) {
      toast.error('Ошибка при создании отчёта');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) resetForm(); onOpenChange(o); }}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Создать публичный отчёт</DialogTitle>
          <DialogDescription>Настройте параметры отчёта для кураторов и родителей</DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Тип отчёта */}
          <div className="space-y-2">
            <Label>Тип отчёта</Label>
            <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="full">Полный отчёт</SelectItem>
                <SelectItem value="attestation_only">Только аттестация</SelectItem>
                <SelectItem value="attendance_only">Только посещаемость</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Срок действия */}
          <div className="space-y-2">
            <Label>Срок действия</Label>
            <Select value={expiresInDays} onValueChange={setExpiresInDays}>
              <SelectTrigger><SelectValue placeholder="Бессрочно" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Бессрочно</SelectItem>
                <SelectItem value="1">1 день</SelectItem>
                <SelectItem value="7">7 дней</SelectItem>
                <SelectItem value="30">30 дней</SelectItem>
                <SelectItem value="90">90 дней</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* PIN-код */}
          <div className="space-y-2">
            <Label>PIN-код (опционально)</Label>
            <Input type="text" placeholder="4-6 цифр" value={pinCode} onChange={(e) => setPinCode(e.target.value.replace(/\D/g, '').slice(0, 6))} maxLength={6} />
            <p className="text-xs text-muted-foreground">Оставьте пустым для открытого доступа</p>
          </div>

          {/* Настройки видимости */}
          <div className="space-y-4">
            <Label className="text-base">Видимость данных</Label>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="show-names" className="font-normal">Имена студентов</Label>
                <Switch id="show-names" checked={showNames} onCheckedChange={setShowNames} />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="show-grades" className="font-normal">Оценки и баллы</Label>
                <Switch id="show-grades" checked={showGrades} onCheckedChange={setShowGrades} />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="show-attendance" className="font-normal">Посещаемость</Label>
                <Switch id="show-attendance" checked={showAttendance} onCheckedChange={setShowAttendance} />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="show-notes" className="font-normal">Заметки</Label>
                <Switch id="show-notes" checked={showNotes} onCheckedChange={setShowNotes} />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="show-rating" className="font-normal">Рейтинг в группе</Label>
                <Switch id="show-rating" checked={showRating} onCheckedChange={setShowRating} />
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            Создать
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
