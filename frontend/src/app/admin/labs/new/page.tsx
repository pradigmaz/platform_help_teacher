'use client';

import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { LabsAPI } from '@/lib/api';
import { LabEditor, LabData } from '@/components/labs';
import { Button } from '@/components/ui/button';
import { IconArrowLeft } from '@tabler/icons-react';
import Link from 'next/link';

export default function NewLabPage() {
  const router = useRouter();

  const handleSave = async (data: LabData) => {
    try {
      const created = await LabsAPI.adminCreate({
        number: data.number,
        title: data.title,
        topic: data.topic,
        goal: data.goal,
        formatting_guide: data.formatting_guide,
        theory_content: data.theory_content as Record<string, unknown>,
        practice_content: data.practice_content as Record<string, unknown>,
        variants: data.variants,
        questions: data.questions,
        max_grade: data.max_grade,
        deadline: data.deadline,
        is_sequential: data.is_sequential,
      });
      toast.success('Лабораторная создана');
      router.push(`/admin/labs/${created.id}/edit`);
    } catch (e) {
      console.error(e);
      toast.error('Ошибка создания');
      throw e;
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <Link href="/admin/labs">
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
