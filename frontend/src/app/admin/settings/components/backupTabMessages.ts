import type {
  BackupCreateResponse,
  RestoreResponse,
  UploadBackupResponse,
  VerifyResponse,
} from '@/lib/api';

export function getVerifyMessage(result: VerifyResponse): string {
  switch (result.status) {
    case 'valid':
      return 'Бэкап валиден';
    case 'recovery_code_required':
      return result.error || 'Для проверки этого бэкапа нужен recovery code';
    case 'invalid_recovery_code':
      return result.error || 'Recovery code неверный';
    case 'dump_invalid':
      return result.error || 'Бэкап расшифровался, но dump не читается через pg_restore';
    default:
      return result.error || 'Проверка бэкапа завершилась ошибкой';
  }
}

export function getRestoreMessage(result: RestoreResponse): string {
  if (result.success) {
    return 'База данных восстановлена';
  }
  switch (result.status) {
    case 'recovery_code_required':
      return result.error || 'Для восстановления этого бэкапа нужен recovery code';
    case 'invalid_recovery_code':
      return result.error || 'Recovery code неверный';
    default:
      return result.error || 'Восстановление завершилось ошибкой';
  }
}

export function getUploadMessage(result: UploadBackupResponse): string {
  if (!result.success) {
    return result.error || 'Ошибка загрузки бэкапа';
  }
  if (result.verification_status === 'recovery_code_required') {
    return 'Файл загружен. Для полной проверки на этой машине понадобится recovery code.';
  }
  if (result.verified === false) {
    return result.error || 'Файл загружен, но полная проверка не прошла';
  }
  return `Бэкап загружен: ${result.backup_key}`;
}

export function getCreateMessage(result: BackupCreateResponse): string {
  if (!result.success) {
    return result.error || 'Ошибка создания бэкапа';
  }
  if (result.mirrored_offsite === false) {
    return `Бэкап создан: ${result.backup_key}. Offsite mirror не удался.`;
  }
  return `Бэкап создан: ${result.backup_key}`;
}
