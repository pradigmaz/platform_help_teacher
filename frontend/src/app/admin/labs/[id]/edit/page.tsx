'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { LabsAPI, Lab } from '@/lib/api';
import { LabEditor, LabData, normalizeVariant } from '@/components/labs';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { IconArrowLeft } from '@tabler/icons-react';
import Link from 'next/link';

export default function EditLabPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const labId = params.id as string;
  const isNew = labId === 'new';
  const subjectId = searchParams.get('subject_id');
  const offeringId = searchParams.get('offering_id');
  const contextQuery = subjectId ? `?subject_id=${subjectId}${offeringId ? `&offering_id=${offeringId}` : ''}` : '';
  const backHref = `/admin/labs${contextQuery}`;

  const [loading, setLoading] = useState(!isNew);
  const [lab, setLab] = useState<Lab | null>(null);

  const loadLab = useCallback(async () => {
    try {
      const data = await LabsAPI.adminGet(labId);
      setLab(data);
    } catch {
      toast.error('Ошибка загрузки лабораторной');
      router.push('/admin/labs');
    } finally {
      setLoading(false);
    }
  }, [labId, router]);

  useEffect(() => {
    if (!isNew) {
      loadLab();
    }
  }, [isNew, loadLab]);

  const handleSave = async (data: LabData) => {
    try {
      if (isNew) {
        const created = await LabsAPI.adminCreate({
          number: data.number,
          title: data.title,
          goal: data.goal,
          formatting_guide: data.formatting_guide,
          theory_content: data.theory_content as unknown as Record<string, unknown>,
          practice_content: data.practice_content as unknown as Record<string, unknown>,
          variants: data.variants,
          questions: data.questions as unknown as string[],
          max_grade: 5,
          deadline_5_lessons: data.deadline_5_lessons,
          deadline_4_lessons: data.deadline_4_lessons,
          is_sequential: data.is_sequential,
          subject_id: data.subject_id ?? subjectId ?? undefined,
        });
        toast.success('Лабораторная создана');
        router.push(`/admin/labs/${created.id}/edit${contextQuery}`);
      } else {
        await LabsAPI.adminUpdate(labId, {
          number: data.number,
          title: data.title,
          goal: data.goal,
          formatting_guide: data.formatting_guide,
          theory_content: data.theory_content as unknown as Record<string, unknown>,
          practice_content: data.practice_content as unknown as Record<string, unknown>,
          variants: data.variants,
          questions: data.questions as unknown as string[],
          max_grade: 5,
          deadline_5_lessons: data.deadline_5_lessons,
          deadline_4_lessons: data.deadline_4_lessons,
          is_sequential: data.is_sequential,
          subject_id: data.subject_id ?? lab?.subject_id,
        });
        toast.success('Лабораторная сохранена');
      }
    } catch (e) {
      console.error(e);
      toast.error('Ошибка сохранения');
      throw e;
    }
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-[600px] rounded-xl" />
      </div>
    );
  }

  const initialData: Partial<LabData> | undefined = lab ? {
    id: lab.id,
    number: lab.number,
    title: lab.title,
    goal: lab.goal || undefined,
    formatting_guide: lab.formatting_guide || undefined,
    theory_content: lab.theory_content as LabData['theory_content'],
    practice_content: lab.practice_content as LabData['practice_content'],
    variants: (lab.variants || []).map(v => normalizeVariant(v)),
    questions: lab.questions || [],
    max_grade: 5,
    deadline_5_lessons: lab.deadline_5_lessons,
    deadline_4_lessons: lab.deadline_4_lessons,
    is_sequential: lab.is_sequential,
    subject_id: lab.subject_id,
  } : undefined;

  return (
    <div className="p-6">
      <div className="mb-6">
        <Link href={backHref}>
          <Button variant="ghost" size="sm">
            <IconArrowLeft className="h-4 w-4 mr-2" />
            Назад к списку
          </Button>
        </Link>
      </div>
      
      <LabEditor
        initialData={initialData}
        onSave={handleSave}
      />
    </div>
  );
}
