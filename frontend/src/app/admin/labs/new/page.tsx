'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { LabsAPI } from '@/lib/api';
import { LabEditor, LabData } from '@/components/labs';
import { Button } from '@/components/ui/button';
import { IconArrowLeft } from '@tabler/icons-react';
import Link from 'next/link';

export default function NewLabPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const subjectId = searchParams.get('subject_id');
  const offeringId = searchParams.get('offering_id');
  const backHref = subjectId
    ? `/admin/labs?subject_id=${subjectId}${offeringId ? `&offering_id=${offeringId}` : ''}`
    : '/admin/labs';

  const handleSave = async (data: LabData) => {
    if (!subjectId) {
      toast.error('Выберите предмет в списке лабораторных');
      router.push('/admin/labs');
      return;
    }
    try {
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
        subject_id: subjectId,
      });
      toast.success('Лабораторная создана');
      router.push(`/admin/labs/${created.id}/edit?subject_id=${subjectId}${offeringId ? `&offering_id=${offeringId}` : ''}`);
    } catch (e) {
      console.error(e);
      toast.error('Ошибка создания');
      throw e;
    }
  };

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
      
      <LabEditor onSave={handleSave} />
    </div>
  );
}
