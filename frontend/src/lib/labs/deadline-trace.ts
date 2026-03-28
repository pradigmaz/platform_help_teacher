type DeadlineTraceLike = {
  lesson_index?: number | null;
  current_max_grade: number;
  extension_bonus: number;
  has_extension: boolean;
  is_excused_origin: boolean;
  effective_deadline_5_lessons?: number | null;
  effective_deadline_4_lessons?: number | null;
  effective_deadline_5_date?: string | null;
  effective_deadline_4_date?: string | null;
};

function formatDeadlineDate(value?: string | null): string | null {
  if (!value) {
    return null;
  }

  const [year, month, day] = value.split('-');
  if (!year || !month || !day) {
    return value;
  }
  return `${day}.${month}`;
}

export function getDeadlineTraceTokens(trace?: DeadlineTraceLike | null): string[] {
  if (!trace) {
    return [];
  }

  const tokens = [`макс. ${trace.current_max_grade}`];

  if (trace.lesson_index !== null && trace.lesson_index !== undefined) {
    tokens.push(`индекс ${trace.lesson_index}`);
  }
  if (trace.has_extension && trace.extension_bonus > 0) {
    tokens.push(`+${trace.extension_bonus} пар`);
  }
  if (trace.is_excused_origin) {
    tokens.push('EXCUSED origin');
  }
  if (trace.effective_deadline_5_lessons !== null && trace.effective_deadline_5_lessons !== undefined) {
    tokens.push(`5→${trace.effective_deadline_5_lessons}`);
  }
  const deadline5Date = formatDeadlineDate(trace.effective_deadline_5_date);
  if (deadline5Date) {
    tokens.push(`5 до ${deadline5Date}`);
  }
  if (trace.effective_deadline_4_lessons !== null && trace.effective_deadline_4_lessons !== undefined) {
    tokens.push(`4→${trace.effective_deadline_4_lessons}`);
  }
  const deadline4Date = formatDeadlineDate(trace.effective_deadline_4_date);
  if (deadline4Date) {
    tokens.push(`4 до ${deadline4Date}`);
  }

  return tokens;
}
