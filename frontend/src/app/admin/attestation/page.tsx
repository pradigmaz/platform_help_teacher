'use client';

import { useRouter } from 'next/navigation';
import { AttestationSettingsForm } from '@/components/admin/AttestationSettingsForm';
import { Button } from '@/components/ui/button';
import { Check } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

export default function AttestationPage() {
  const router = useRouter();

  const handleComplete = async () => {
    try {
      await api.patch('/users/me', { onboarding_completed: true });
      toast.success('Настройки аттестации сохранены');
      router.push('/admin');
    } catch {
      toast.error('Ошибка сохранения');
    }
  };

  return (
    <div className="space-y-6">
      <AttestationSettingsForm />
      <div className="flex justify-end">
        <Button onClick={handleComplete} className="bg-gradient-to-r from-green-500 to-emerald-600">
          <Check className="w-4 h-4 mr-2" />
          Готово, использовать эти настройки
        </Button>
      </div>
    </div>
  );
}
