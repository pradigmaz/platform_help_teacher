'use client';

import { IconFlask } from '@tabler/icons-react';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import type { FilterStatus } from '../types';

interface LabsEmptyStateProps {
  filter: FilterStatus;
  mustChooseSubject: boolean;
  subjectScopeError: boolean;
}

export function LabsEmptyState({ filter, mustChooseSubject, subjectScopeError }: LabsEmptyStateProps) {
  const title = subjectScopeError
    ? 'Не удалось определить предмет'
    : mustChooseSubject ? 'Сначала выберите предмет' : filter === 'all' ? 'Нет лабораторных работ' : 'Нет работ с таким статусом';
  const description = subjectScopeError
    ? 'Лабораторные не будут загружены без предметного контекста. Обновите страницу или проверьте настройки группы.'
    : mustChooseSubject
    ? 'После выбора предмета появятся лабораторные именно по нему.'
    : filter === 'all'
      ? 'Лабораторные работы появятся здесь, когда преподаватель их добавит'
      : 'Попробуйте выбрать другой фильтр';

  return (
    <CardSpotlight className="p-12 text-center">
      <IconFlask className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </CardSpotlight>
  );
}
