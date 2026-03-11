export const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  view: { label: "Просмотр", color: "bg-blue-500/10 text-blue-500" },
  create: { label: "Создание", color: "bg-green-500/10 text-green-500" },
  update: { label: "Изменение", color: "bg-yellow-500/10 text-yellow-500" },
  delete: { label: "Удаление", color: "bg-red-500/10 text-red-500" },
  auth_login: { label: "Вход", color: "bg-purple-500/10 text-purple-500" },
  auth_logout: { label: "Выход", color: "bg-gray-500/10 text-gray-500" },
  submit: { label: "Сдача", color: "bg-emerald-500/10 text-emerald-500" },
  cancel: { label: "Отмена", color: "bg-orange-500/10 text-orange-500" },
  error: { label: "Ошибка", color: "bg-red-500/10 text-red-500" },
  bot_start: { label: "Бот /start", color: "bg-cyan-500/10 text-cyan-500" },
  bot_auth: { label: "Бот OTP", color: "bg-indigo-500/10 text-indigo-500" },
  bot_bind: { label: "Бот привязка", color: "bg-teal-500/10 text-teal-500" },
  bot_relink: { label: "Бот перепривязка", color: "bg-amber-500/10 text-amber-500" },
  bot_message: { label: "Бот сообщение", color: "bg-slate-500/10 text-slate-500" },
};

const DEFAULT_ACTOR_ROLE = {
  label: "Неизвестно",
  color: "bg-muted text-muted-foreground border-border",
};

export const ACTOR_ROLE_LABELS: Record<string, { label: string; color: string }> = {
  student: { label: "Студент", color: "bg-emerald-500/10 text-emerald-700 border-emerald-500/20 dark:text-emerald-400" },
  teacher: { label: "Преподаватель", color: "bg-blue-500/10 text-blue-700 border-blue-500/20 dark:text-blue-400" },
  admin: { label: "Админ", color: "bg-amber-500/10 text-amber-700 border-amber-500/20 dark:text-amber-400" },
  anonymous: { label: "Аноним", color: "bg-muted text-muted-foreground border-border" },
};

export function getActorRoleMeta(actorRole?: string | null) {
  if (!actorRole) {
    return null;
  }

  const normalizedRole = actorRole.toLowerCase();

  return ACTOR_ROLE_LABELS[normalizedRole] ?? {
    label: actorRole,
    color: DEFAULT_ACTOR_ROLE.color,
  };
}

export function formatAuditDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
