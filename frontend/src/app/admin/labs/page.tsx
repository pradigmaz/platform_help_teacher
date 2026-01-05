'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Plus, Pencil, Trash2, FlaskConical, Settings, Calendar, Award } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

// Magic UI / Aceternity компоненты
import { BlurFade } from '@/components/ui/blur-fade';
import { MagicCard } from '@/components/ui/magic-card';
import { BorderBeam } from '@/components/ui/border-beam';
import { NumberTicker } from '@/components/ui/number-ticker';
import { Sparkles } from '@/components/ui/sparkles';
import { AnimatedCircularProgress } from '@/components/ui/animated-circular-progress';


interface Lab {
  id: string;
  title: string;
  description: string | null;
  max_grade: number;
  deadline: string | null;
  created_at: string;
}

interface LabForm {
  title: string;
  description: string;
  max_grade: number;
  deadline: string;
}

interface LabSettings {
  labs_count: number;
  grading_scale: '5' | '10' | '100';
  default_max_grade: number;
}

const GRADING_SCALES = [
  { value: '5', label: '5-балльная' },
  { value: '10', label: '10-балльная' },
  { value: '100', label: '100-балльная' },
];

const initialForm: LabForm = {
  title: '',
  description: '',
  max_grade: 10,
  deadline: '',
};

export default function AdminLabsPage() {
  const [labs, setLabs] = useState<Lab[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [editingLab, setEditingLab] = useState<Lab | null>(null);
  const [form, setForm] = useState<LabForm>(initialForm);
  const [labSettings, setLabSettings] = useState<LabSettings>({
    labs_count: 10,
    grading_scale: '10',
    default_max_grade: 10,
  });


  useEffect(() => {
    fetchLabs();
    fetchSettings();
  }, []);

  const fetchLabs = async () => {
    try {
      const response = await api.get('/admin/labs');
      setLabs(response.data);
    } catch (error) {
      toast.error('Ошибка загрузки лабораторных работ');
    } finally {
      setLoading(false);
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await api.get('/admin/lab-settings');
      setLabSettings(response.data);
    } catch (error) {
      toast.error('Ошибка загрузки настроек');
      console.error(error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = { ...form, deadline: form.deadline || null };
      
      if (editingLab) {
        await api.patch(`/admin/labs/${editingLab.id}`, payload);
        toast.success('Лабораторная работа обновлена');
      } else {
        await api.post('/admin/labs', payload);
        toast.success('Лабораторная работа создана');
      }
      setDialogOpen(false);
      setEditingLab(null);
      setForm(initialForm);
      fetchLabs();
    } catch (error) {
      toast.error('Ошибка сохранения');
    }
  };

  const handleEdit = (lab: Lab) => {
    setEditingLab(lab);
    setForm({
      title: lab.title,
      description: lab.description || '',
      max_grade: lab.max_grade,
      deadline: lab.deadline ? lab.deadline.split('T')[0] : '',
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить лабораторную работу?')) return;
    try {
      await api.delete(`/admin/labs/${id}`);
      toast.success('Удалено');
      fetchLabs();
    } catch (error) {
      toast.error('Ошибка удаления');
    }
  };

  const openCreateDialog = () => {
    setEditingLab(null);
    setForm({ ...initialForm, max_grade: labSettings.default_max_grade });
    setDialogOpen(true);
  };

  const handleSaveSettings = async () => {
    try {
      await api.patch('/admin/lab-settings', labSettings);
      toast.success('Настройки сохранены');
      setSettingsDialogOpen(false);
    } catch (error) {
      toast.error('Ошибка сохранения настроек');
    }
  };

  const handleGradingScaleChange = (scale: '5' | '10' | '100') => {
    const maxGrades: Record<string, number> = { '5': 5, '10': 10, '100': 100 };
    setLabSettings({ ...labSettings, grading_scale: scale, default_max_grade: maxGrades[scale] });
  };

  // Статистика
  const completedLabs = labs.length;
  const progressPercent = labSettings.labs_count > 0 ? Math.round((completedLabs / labSettings.labs_count) * 100) : 0;

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="h-10 w-64 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="h-32 bg-muted animate-pulse rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <BlurFade delay={0.1}>
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <Sparkles color="#8b5cf6">
                <FlaskConical className="h-8 w-8 text-primary" />
              </Sparkles>
              Лабораторные работы
            </h1>
            <p className="text-muted-foreground mt-1">Управление лабораторными и настройками аттестации</p>
          </div>
        </div>
      </BlurFade>

      {/* Labs Content */}
      <div className="space-y-6 mt-6">
          {/* Labs Header Actions */}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setSettingsDialogOpen(true)}>
              <Settings className="mr-2 h-4 w-4" /> Настройки
            </Button>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={openCreateDialog} className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90">
                  <Plus className="mr-2 h-4 w-4" /> Создать
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <form onSubmit={handleSubmit}>
                  <DialogHeader>
                    <DialogTitle>{editingLab ? 'Редактировать' : 'Новая лабораторная'}</DialogTitle>
                    <DialogDescription>
                      {editingLab ? 'Измените данные лабораторной работы' : 'Заполните данные для создания'}
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <Label htmlFor="title">Название</Label>
                      <Input id="title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Лабораторная работа №1" required />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="description">Описание</Label>
                      <Textarea id="description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Описание задания..." rows={3} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label htmlFor="max_grade">Макс. балл</Label>
                        <Input id="max_grade" type="number" min={1} value={form.max_grade} onChange={(e) => setForm({ ...form, max_grade: parseInt(e.target.value) || 10 })} />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="deadline">Дедлайн</Label>
                        <Input id="deadline" type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} />
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="submit">{editingLab ? 'Сохранить' : 'Создать'}</Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <BlurFade delay={0.15}>
          <MagicCard className="cursor-pointer group" gradientColor="#8b5cf620">
            <div className="p-6 text-center relative overflow-hidden">
              <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <FlaskConical className="w-12 h-12 text-purple-500" />
              </div>
              <div className="text-4xl font-bold text-purple-600 dark:text-purple-400">
                <NumberTicker value={completedLabs} />
              </div>
              <div className="text-sm text-muted-foreground mt-1 font-medium">Создано лаб</div>
            </div>
          </MagicCard>
        </BlurFade>

        <BlurFade delay={0.2}>
          <MagicCard className="cursor-pointer group" gradientColor="#3b82f620">
            <div className="p-6 text-center relative overflow-hidden">
              <div className="absolute top-2 right-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <Calendar className="w-12 h-12 text-blue-500" />
              </div>
              <div className="text-4xl font-bold text-blue-600 dark:text-blue-400">
                <NumberTicker value={labSettings.labs_count} />
              </div>
              <div className="text-sm text-muted-foreground mt-1 font-medium">Запланировано</div>
            </div>
          </MagicCard>
        </BlurFade>

        <BlurFade delay={0.25}>
          <MagicCard className="cursor-pointer group" gradientColor="#22c55e20">
            <div className="p-6 flex items-center justify-center gap-4">
              <AnimatedCircularProgress
                value={progressPercent}
                size={80}
                strokeWidth={6}
                gradientFrom="#22c55e"
                gradientTo="#10b981"
                label=""
              />
              <div>
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">{progressPercent}%</div>
                <div className="text-sm text-muted-foreground">Прогресс</div>
              </div>
            </div>
          </MagicCard>
        </BlurFade>
      </div>

      {/* Settings Info Card */}
      <BlurFade delay={0.3}>
        <Card className="relative overflow-hidden bg-gradient-to-r from-background via-background to-primary/5">
          <BorderBeam size={200} duration={10} />
          <CardContent className="pt-4">
            <div className="flex items-center gap-6 text-sm">
              <span className="font-medium flex items-center gap-2">
                <Award className="w-4 h-4 text-yellow-500" />
                Текущие настройки:
              </span>
              <Badge variant="outline" className="bg-purple-500/10 border-purple-500/30">
                Лаб: {labSettings.labs_count}
              </Badge>
              <Badge variant="outline" className="bg-blue-500/10 border-blue-500/30">
                Шкала: {GRADING_SCALES.find(s => s.value === labSettings.grading_scale)?.label}
              </Badge>
              <Badge variant="outline" className="bg-green-500/10 border-green-500/30">
                Макс. балл: {labSettings.default_max_grade}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </BlurFade>

      {/* Labs Table */}
      <BlurFade delay={0.35}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FlaskConical className="w-5 h-5" />
              Список лабораторных
            </CardTitle>
            <CardDescription>Всего: {labs.length}</CardDescription>
          </CardHeader>
          <CardContent>
            {labs.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground">
                <FlaskConical className="w-16 h-16 mx-auto mb-4 opacity-20" />
                <p className="text-lg">Нет лабораторных работ</p>
                <p className="text-sm">Создайте первую лабораторную работу</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Название</TableHead>
                    <TableHead>Макс. балл</TableHead>
                    <TableHead>Дедлайн</TableHead>
                    <TableHead>Создано</TableHead>
                    <TableHead className="text-right">Действия</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {labs.map((lab) => (
                    <TableRow key={lab.id} className="group hover:bg-muted/50">
                      <TableCell className="font-medium">{lab.title}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="bg-gradient-to-r from-purple-500/20 to-blue-500/20">
                          {lab.max_grade}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {lab.deadline ? (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {new Date(lab.deadline).toLocaleDateString('ru-RU')}
                          </span>
                        ) : '—'}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(lab.created_at).toLocaleDateString('ru-RU')}
                      </TableCell>
                      <TableCell className="text-right space-x-1">
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(lab)} className="opacity-0 group-hover:opacity-100 transition-opacity">
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(lab.id)} className="opacity-0 group-hover:opacity-100 transition-opacity">
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </BlurFade>
      </div>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onOpenChange={setSettingsDialogOpen}>
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
                value={labSettings.labs_count} 
                onChange={(e) => setLabSettings({ ...labSettings, labs_count: parseInt(e.target.value) || 10 })} 
              />
              <p className="text-xs text-muted-foreground">Сколько лабораторных работ в семестре</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSettingsDialogOpen(false)}>Отмена</Button>
            <Button onClick={handleSaveSettings}>Сохранить</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
