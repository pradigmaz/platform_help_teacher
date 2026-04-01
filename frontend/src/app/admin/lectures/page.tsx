'use client';

import { useRouter } from 'next/navigation';
import type { SerializedEditorState } from 'lexical';
import { Card, CardContent } from '@/components/ui/card';
import { BookOpen } from 'lucide-react';
import { toast } from 'sonner';
import { BlurFade } from '@/components/ui/blur-fade';
import { BorderBeam } from '@/components/ui/border-beam';
import { NumberTicker } from '@/components/ui/number-ticker';
import { Sparkles } from '@/components/ui/sparkles';
import LecturesAPI from '@/lib/lectures-api';
import { LectureCard, CreateLectureDialog, useLectures } from '@/components/lectures/admin';

export default function AdminLecturesPage() {
  const router = useRouter();
  const {
    subjects,
    loading,
    selectedSubjectId,
    setSelectedSubjectId,
    lecturesBySubject,
    filteredLectures,
    handleDelete,
    handlePublish,
    handleUnpublish,
    handleCopyLink,
    handleExportPdf,
    handleExportMarkdown,
  } = useLectures();

  const handleCreate = async (title: string, subjectId: string | null) => {
    try {
      const lecture = await LecturesAPI.create({
        title,
        content: { root: { children: [], direction: null, format: '', indent: 0, type: 'root', version: 1 } } as unknown as SerializedEditorState,
        subject_id: subjectId,
      });
      toast.success('Лекция создана');
      router.push(`/admin/lectures/${lecture.id}`);
    } catch (error) {
      toast.error('Ошибка создания лекции');
      throw error;
    }
  };

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
          <CreateLectureDialog subjects={subjects} onSubmit={handleCreate} />
        </div>
      </BlurFade>

      {/* Stats by Subject */}
      <BlurFade delay={0.15}>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <Card
            className={`cursor-pointer border-border/60 bg-card/95 shadow-sm transition-all hover:border-border hover:shadow-md ${!selectedSubjectId ? 'ring-2 ring-primary' : ''}`}
            onClick={() => setSelectedSubjectId(null)}
          >
            <div className="p-4 text-center">
              <div className="text-2xl font-bold text-foreground">
                <NumberTicker value={filteredLectures.length} />
              </div>
              <div className="text-xs text-muted-foreground mt-1 font-medium">Все лекции</div>
            </div>
          </Card>

          {subjects.map((subject) => {
            const count = lecturesBySubject[subject.id]?.lectures.length || 0;
            const isSelected = selectedSubjectId === subject.id;
            return (
              <Card
                key={subject.id}
                className={`cursor-pointer border-border/60 bg-card/95 shadow-sm transition-all hover:border-border hover:shadow-md ${isSelected ? 'ring-2 ring-primary' : ''}`}
                onClick={() => setSelectedSubjectId(isSelected ? null : subject.id)}
              >
                <div className="p-4 text-center">
                  <div className="text-2xl font-bold text-foreground">
                    <NumberTicker value={count} />
                  </div>
                  <div className="text-xs text-muted-foreground mt-1 font-medium truncate" title={subject.name}>
                    {subject.code || subject.name.slice(0, 10)}
                  </div>
                </div>
              </Card>
            );
          })}

          {lecturesBySubject['none']?.lectures.length > 0 && (
            <Card
              className={`cursor-pointer border-border/60 bg-card/95 shadow-sm transition-all hover:border-border hover:shadow-md ${selectedSubjectId === 'none' ? 'ring-2 ring-primary' : ''}`}
              onClick={() => setSelectedSubjectId(selectedSubjectId === 'none' ? null : 'none')}
            >
              <div className="p-4 text-center">
                <div className="text-2xl font-bold text-foreground">
                  <NumberTicker value={lecturesBySubject['none'].lectures.length} />
                </div>
                <div className="text-xs text-muted-foreground mt-1 font-medium">Без предмета</div>
              </div>
            </Card>
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
              <CreateLectureDialog subjects={subjects} onSubmit={handleCreate} />
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredLectures.map((lecture, index) => (
              <BlurFade key={lecture.id} delay={0.1 + index * 0.05}>
                <LectureCard
                  lecture={lecture}
                  onDelete={handleDelete}
                  onPublish={handlePublish}
                  onUnpublish={handleUnpublish}
                  onCopyLink={handleCopyLink}
                  onExportPdf={handleExportPdf}
                  onExportMarkdown={handleExportMarkdown}
                />
              </BlurFade>
            ))}
          </div>
        )}
      </BlurFade>
    </div>
  );
}
