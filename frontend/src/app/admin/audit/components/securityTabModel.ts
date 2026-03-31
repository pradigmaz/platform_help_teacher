import type {
  SecurityStatsResponse,
  SecurityStrikesResponse,
  UserInfoResponse,
} from '@/lib/api';
import {
  AlertTriangle,
  Bug,
  FileWarning,
  Link2Off,
  Skull,
} from 'lucide-react';

export const ATTACK_TYPE_INFO: Record<string, { icon: typeof Bug; label: string; color: string }> = {
  sql_injection: { icon: Bug, label: 'SQL Injection', color: 'text-red-500' },
  path_traversal: { icon: FileWarning, label: 'Path Traversal', color: 'text-orange-500' },
  xss: { icon: Skull, label: 'XSS', color: 'text-purple-500' },
  idor: { icon: Link2Off, label: 'IDOR', color: 'text-yellow-500' },
  unknown: { icon: AlertTriangle, label: 'Неизвестно', color: 'text-gray-500' },
};

export function extractSecurityUserIds(bans: SecurityStrikesResponse[]): string[] {
  return bans
    .filter((ban) => ban.identifier.startsWith('user:'))
    .map((ban) => ban.identifier.replace('user:', ''));
}

export function buildSecurityUserInfoMap(
  entries: Array<{ userId: string; info: UserInfoResponse } | null>
): Record<string, UserInfoResponse> {
  return entries.reduce<Record<string, UserInfoResponse>>((accumulator, entry) => {
    if (entry) {
      accumulator[entry.userId] = entry.info;
    }
    return accumulator;
  }, {});
}

export function formatSecurityBanTimeLeft(ttl: number | null): string {
  if (!ttl || ttl <= 0) {
    return 'Истёк';
  }
  const minutes = Math.floor(ttl / 60);
  if (minutes < 60) {
    return `${minutes} мин`;
  }
  const hours = Math.floor(minutes / 60);
  return `${hours} ч ${minutes % 60} мин`;
}

export function hasTopAttackTypes(stats: SecurityStatsResponse | null): boolean {
  return Boolean(stats && Object.keys(stats.top_attack_types).length > 0);
}
