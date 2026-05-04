'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { LabsAPI, Lab } from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';
import { LabViewHeader, LabInfoBadges, LabContentTabs, LabQuestions } from '@/components/labs';

export default function LabViewPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const labId = params.id as string;
  const subjectId = searchParams.get('subject_id');
  const offeringId = searchParams.get('offering_id');
  const contextQuery = subjectId ? `?subject_id=${subjectId}${offeringId ? `&offering_id=${offeringId}` : ''}` : '';

  const [loading, setLoading] = useState(true);
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
    loadLab();
  }, [loadLab]);

  const handleDelete = () => {
    router.push(`/admin/labs${contextQuery}`);
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
      <LabViewHeader lab={lab} onLabUpdate={setLab} onDelete={handleDelete} contextQuery={contextQuery} />
      <LabInfoBadges lab={lab} />
      <LabContentTabs lab={lab} />
      <LabQuestions lab={lab} />
    </div>
  );
}
