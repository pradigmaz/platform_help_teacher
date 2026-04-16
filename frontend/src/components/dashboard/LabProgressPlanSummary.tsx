'use client';

import type { StudentAttestation } from '@/lib/api';

interface LabProgressPlanSummaryProps {
  attestation: StudentAttestation | null;
}

function getThresholdNote(remaining: number): string {
  return remaining <= 0 ? 'Требование закрыто' : `Осталось ${remaining}`;
}

function formatAutomaticPlaces(value: number): string {
  const mod10 = value % 10;
  const mod100 = value % 100;

  if (mod10 === 1 && mod100 !== 11) {
    return `${value} место`;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `${value} места`;
  }
  return `${value} мест`;
}

function getAutomaticProgressNote(plan: NonNullable<StudentAttestation['lab_progress_plan']>): string {
  if (!plan.automatic_enabled) {
    if (plan.automatic_reason === 'not_exam') {
      return 'Автоматы доступны только по экзамену';
    }
    if (plan.automatic_reason === 'subject_required') {
      return 'Выберите предмет, чтобы увидеть автомат';
    }
    return 'Сейчас действует режим без автоматов';
  }
  if (plan.automatic_declined) {
    return 'Автомат снят администратором, действует обычный путь';
  }
  if (plan.automatic_remaining > 0) {
    return `Осталось ${plan.automatic_remaining}`;
  }
  if (plan.automatic_is_winner) {
    return 'Автомат получен';
  }
  if (plan.automatic_queue_position) {
    return `Место не досталось, очередь: ${plan.automatic_queue_position}`;
  }
  return 'Все лабы закрыты';
}

function getAutomaticPlacesNote(plan: NonNullable<StudentAttestation['lab_progress_plan']>): string {
  if (!plan.automatic_enabled) {
    if (plan.automatic_reason === 'not_exam') {
      return 'Для зачёта и дифзачёта квота не используется';
    }
    return 'Учитываются только обычные аттестации';
  }
  if (plan.automatic_places === null || plan.automatic_places === undefined) {
    return 'Квота не задана';
  }
  if (plan.automatic_queue_position) {
    return `Кто первый закроет все лабы`;
  }
  return 'Кто первый закроет все лабы';
}

export function LabProgressPlanSummary({ attestation }: LabProgressPlanSummaryProps) {
  const plan = attestation?.lab_progress_plan;
  if (!plan) {
    return null;
  }

  const firstRemaining = Math.max(plan.first_required - plan.completed_count, 0);
  const secondRemaining = Math.max(plan.second_total_required - plan.completed_count, 0);

  const cards = [
    {
      title: '1-я аттестация',
      value: `${plan.first_required} лаб.`,
      note: getThresholdNote(firstRemaining),
    },
    {
      title: '2-я аттестация',
      value: `Ещё ${plan.second_extra_required}, всего ${plan.second_total_required}`,
      note: getThresholdNote(secondRemaining),
    },
    {
      title: 'Автоматы',
      value: plan.automatic_enabled
        ? plan.automatic_extra_required > 0
          ? `Ещё ${plan.automatic_extra_required}, всего ${plan.total_required}`
          : `Всего ${plan.total_required}`
        : 'Отключены',
      note: getAutomaticProgressNote(plan),
    },
    {
      title: 'Места на автомат',
      value:
        plan.automatic_enabled && plan.automatic_places !== null && plan.automatic_places !== undefined
          ? formatAutomaticPlaces(plan.automatic_places)
          : 'Не используются',
      note: getAutomaticPlacesNote(plan),
    },
  ];

  return (
    <div className="mt-5 space-y-3 border-t border-border/50 pt-4">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>План по лабораторным</span>
        <span>
          Зачтено: <span className="font-semibold text-foreground">{plan.completed_count}/{plan.total_required}</span>
        </span>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(card => (
          <div key={card.title} className="rounded-lg border border-border/50 bg-background/60 p-3">
            <p className="text-xs font-medium text-muted-foreground">{card.title}</p>
            <p className="mt-1 text-sm font-semibold text-foreground">{card.value}</p>
            <p className="mt-1 text-xs text-muted-foreground">{card.note}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
