'use client';

import { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Plus, 
  FileText, 
  MoreVertical, 
  Pencil, 
  Trash2, 
  Link2, 
  Link2Off, 
  Download,
  Copy,
  ExternalLink,
  BookOpen,
  GraduationCap
} from 'lucide-react';
import { toast } from 'sonner';
import { BlurFade } from '@/components/ui/blur-fade';
import { MagicCard } from '@/components/ui/magic-card';
import { BorderBeam } from '@/components/ui/border-beam';
import { NumberTicker } from '@/components/ui/number-ticker';
import { Sparkles } from '@/components/ui/sparkles';
import LecturesAPI, { LectureListResponse, SubjectBrief } from '@/lib/lectures-api';
import api from '@/lib/api';

interface Subject {
  id: string;
  name: string;
  code: string | null;
  is_active: boolean;
}

export default function AdminLecturesPage() {
  const router = useRouter();
  const [lectures, setLectures] = useState<LectureListResponse[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newSubjectId, setNewSubjectId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [lecturesData, subjectsData] = await Promise.all([
        LecturesAPI.list(),
        api.get<Subject[]>('/admin/subjects/').then(r => r.data)
      ]);
      setLectures(lecturesData);
      setSubjects(subjectsData);
    } catch (error) {
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  // Группировка лекций по предметам
  const lecturesBySubject = useMemo(() => {
    const grouped: Record<string, { subject: SubjectBrief | null; lectures: LectureListResponse[] }> = {};
    
    // Группа "Без предмета"
    grouped['none'] = { subject: null, lectures: [] };
    
    // Инициализируем группы для всех предметов
    subjects.forEach(s => {
      grouped[s.id] = { subject: { id: s.id, name: s.name, code: s.code }, lectures: [] };
    });
    
    // Распределяем лекции
    lectures.forEach(lecture => {
      const key = lecture.subject_id || 'none';
      if (grouped[key]) {
        grouped[key].lectures.push(lecture);
      } else {
        grouped['none'].lectures.push(lecture);
      }
    });
    
    return grouped;
  }, [lectures, subjects]);

  // Фильтрованные лекции
  const filteredLectures = useMemo(() => {
    if (!selectedSubjectId) return lectures;
    if (selectedSubjectId === 'none') return lectures.filter(l => !l.subject_id);
    return lectures.filter(l => l.subject_id === selectedSubjectId);
  }, [lectures, selectedSubjectId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    
    setCreating(true);
    try {
      const lecture = await LecturesAPI.create({
        title: newTitle.trim(),
        content: { root: { children: [], direction: null, format: '', indent: 0, type: 'root', version: 1 } } as any,
        subject_id: newSubjectId,
      });
      toast.success('Лекция создана');
      setCreateDialogOpen(false);
      setNewTitle('');
      setNewSubjectId(null);
      router.push(`/admin/lectures/${lecture.id}`);
    } catch (error) {
      toast.error('Ошибка создания лекции');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string, title: string) => {
    if (!confirm(`Удалить лекцию "${title}"?`)) return;
    try {
      await LecturesAPI.delete(id);
      toast.success('Лекция удалена');
      fetchData();
    } catch (error) {
      toast.error('Ошибка удаления');
    }
  };

  const handlePublish = async (id: string) => {
    try {
      const result = await LecturesAPI.publish(id);
      toast.success('Лекция опубликована');
      await navigator.clipboard.writeText(`${window.location.origin}/lectures/view/${result.public_code}`);
      toast.info('Ссылка скопирована');
      fetchData();
    } catch (error) {
      toast.error('Ошибка публикации');
    }
  };

  const handleUnpublish = async (id: string) => {
    try {
      await LecturesAPI.unpublish(id);
      toast.success('Публикация отменена');
      fetchData();
    } catch (error) {
      toast.error('Ошибка');
    }
  };

  const handleCopyLink = async (code: string) => {
    await navigator.clipboard.writeText(`${window.location.origin}/lectures/view/${code}`);
    toast.success('Ссылка скопирована');
  };

  const handleExportPdf = async (id: string, title: string) => {
    try {
      toast.info('Генерация PDF...');
      const blob = await LecturesAPI.exportPdf(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('PDF скачан');
    } catch (error) {
      toast.error('Ошибка экспорта PDF');
    }
  };

  const publishedCount = lectures.filter(l => l.is_published).length;

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="h-10 w-64 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="h-48 bg-muted animate-pulse rounded-xl" />)}
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
                <BookOpen className="h-8 w-8 text-primary" />
              </Sparkles>
              Лекции
            </h1>
            <p className="text-muted-foreground mt-1">Создание и управление интерактивными лекциями</p>
          </div>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90">
                <Plus className="mr-2 h-4 w-4" /> Создать лекцию
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[400px]">
              <form onSubmit={handleCreate}>
                <DialogHeader>
                  <DialogTitle>Новая лекция</DialogTitle>
                  <DialogDescription>Введите название и выберите предмет</DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="title">Название</Label>
                    <Input
                      id="title"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      placeholder="Введение в алгоритмы"
                      required
                      autoFocus
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="subject">Предмет</Label>
                    <Select value={newSubjectId || ''} onValueChange={(v) => setNewSubjectId(v || null)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Выберите предмет (опционально)" />
                      </SelectTrigger>
                      <SelectContent>
                        {subjects.map(subject => (
                          <SelectItem key={subject.id} value={subject.id}>
                            {subject.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setCreateDialogOpen(false)}>
                    Отмена
                  </Button>
                  <Button type="submit" disabled={creating || !newTitle.trim()}>
                    {creating ? 'Создание...' : 'Создать'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </BlurFade>

      {/* Stats by Subject */}
      <BlurFade delay={0.15}>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {/* Все лекции */}
          <MagicCard 
            className={`cursor-pointer transition-all ${!selectedSubjectId ? 'ring-2 ring-primary' : ''}`}
            gradientColor="#8b5cf620"
            onClick={() => setSelectedSubjectId(null)}
          >
            <div className="p-4 text-center">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                <NumberTicker value={lectures.length} />
              </div>
              <div className="text-xs text-muted-foreground mt-1 font-medium">Все лекции</div>
            </div>
          </MagicCard>

          {/* По предметам */}
          {subjects.map((subject, idx) => {
            const count = lecturesBySubject[subject.id]?.lectures.length || 0;
            const isSelected = selectedSubjectId === subject.id;
            return (
              <MagicCard 
                key={subject.id}
                className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-primary' : ''}`}
                gradientColor="#3b82f620"
                onClick={() => setSelectedSubjectId(isSelected ? null : subject.id)}
              >
                <div className="p-4 text-center">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    <NumberTicker value={count} />
                  </div>
                  <div className="text-xs text-muted-foreground mt-1 font-medium truncate" title={subject.name}>
                    {subject.code || subject.name.slice(0, 10)}
                  </div>
                </div>
              </MagicCard>
            );
          })}

          {/* Без предмета */}
          {lecturesBySubject['none']?.lectures.length > 0 && (
            <MagicCard 
              className={`cursor-pointer transition-all ${selectedSubjectId === 'none' ? 'ring-2 ring-primary' : ''}`}
              gradientColor="#71717a20"
              onClick={() => setSelectedSubjectId(selectedSubjectId === 'none' ? null : 'none')}
            >
              <div className="p-4 text-center">
                <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                  <NumberTicker value={lecturesBySubject['none'].lectures.length} />
                </div>
                <div className="text-xs text-muted-foreground mt-1 font-medium">Без предмета</div>
              </div>
            </MagicCard>
          )}
        </div>
      </BlurFade>

      {/* Lectures Grid */}
      <BlurFade delay={0.3}>
        {filteredLectures.length === 0 ? (
          <Card className="relative overflow-hidden">
            <BorderBeam size={200} duration={10} />
            <CardContent className="py-16 text-center">
              <BookOpen className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg text-muted-foreground">
                {selectedSubjectId ? 'Нет лекций по этому предмету' : 'Нет лекций'}
              </p>
              <p className="text-sm text-muted-foreground mb-4">Создайте первую интерактивную лекцию</p>
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" /> Создать лекцию
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredLectures.map((lecture, index) => (
              <BlurFade key={lecture.id} delay={0.1 + index * 0.05}>
                <MagicCard 
                  className="cursor-pointer group h-full" 
                  gradientColor={lecture.is_published ? '#22c55e20' : '#8b5cf620'}
                >
                  <div className="p-5 h-full flex flex-col">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1 min-w-0">
                        <h3 
                          className="font-semibold text-lg truncate hover:text-primary transition-colors cursor-pointer"
                          onClick={() => router.push(`/admin/lectures/${lecture.id}`)}
                        >
                          {lecture.title}
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          {new Date(lecture.updated_at).toLocaleDateString('ru-RU', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </p>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => router.push(`/admin/lectures/${lecture.id}`)}>
                            <Pencil className="mr-2 h-4 w-4" /> Редактировать
                          </DropdownMenuItem>
                          {lecture.is_published ? (
                            <>
                              <DropdownMenuItem onClick={() => handleCopyLink(lecture.public_code!)}>
                                <Copy className="mr-2 h-4 w-4" /> Копировать ссылку
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => window.open(`/lectures/view/${lecture.public_code}`, '_blank')}>
                                <ExternalLink className="mr-2 h-4 w-4" /> Открыть
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleUnpublish(lecture.id)}>
                                <Link2Off className="mr-2 h-4 w-4" /> Снять публикацию
                              </DropdownMenuItem>
                            </>
                          ) : (
                            <DropdownMenuItem onClick={() => handlePublish(lecture.id)}>
                              <Link2 className="mr-2 h-4 w-4" /> Опубликовать
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem onClick={() => handleExportPdf(lecture.id, lecture.title)}>
                            <Download className="mr-2 h-4 w-4" /> Экспорт PDF
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(lecture.id, lecture.title)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="mr-2 h-4 w-4" /> Удалить
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    <div className="mt-auto pt-3 flex items-center gap-2 flex-wrap">
                      {lecture.subject && (
                        <Badge variant="outline" className="text-xs">
                          <GraduationCap className="mr-1 h-3 w-3" />
                          {lecture.subject.code || lecture.subject.name}
                        </Badge>
                      )}
                      {lecture.is_published ? (
                        <Badge variant="secondary" className="bg-green-500/10 text-green-600 border-green-500/30">
                          <Link2 className="mr-1 h-3 w-3" /> Опубликовано
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="bg-muted">
                          Черновик
                        </Badge>
                      )}
                    </div>
                  </div>
                </MagicCard>
              </BlurFade>
            ))}
          </div>
        )}
      </BlurFade>
    </div>
  );
}
