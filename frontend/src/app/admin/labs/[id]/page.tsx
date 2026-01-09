'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { LabsAPI, Lab } from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';
import { LabViewHeader, LabInfoBadges, LabContentTabs, LabQuestions } from '@/components/labs';

export default function LabViewPage() {
  const params = useParams();
  const router = useRouter();
  const labId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [lab, setLab] = useState<Lab | null>(null);

  useEffect(() => {
    loadLab();
  }, [labId]);

  const loadLab = async () => {
    try {
      const data = await LabsAPI.adminGet(labId);
      setLab(data);
    } catch {
      toast.error('Ошибка загрузки лабораторной');
      router.push('/admin/labs');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = () => {
    router.push('/admin/labs');
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-[600px] rounded-xl" />
      </div>
    );
  }

  if (!lab) return null;

  return (
    <div className="p-6 space-y-6">
      <LabViewHeader lab={lab} onLabUpdate={setLab} onDelete={handleDelete} />
      <LabInfoBadges lab={lab} />
      <LabContentTabs lab={lab} />
      <LabQuestions lab={lab} />
    </div>
  );
}
