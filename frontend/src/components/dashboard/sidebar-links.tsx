'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { BookOpenText } from 'lucide-react';
import {
  IconCalendar,
  IconFlask,
  IconLayoutDashboard,
  IconSettings,
  IconStar,
} from '@tabler/icons-react';
import { cn } from '@/lib/utils';

export interface SidebarLinkItem {
  label: string;
  href: string;
  icon: ReactNode;
}

export function NavLink({
  link,
  open,
  onClick,
}: {
  link: SidebarLinkItem;
  open: boolean;
  onClick?: () => void;
}) {
  return (
    <Link
      href={link.href}
      className="flex items-center justify-start gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-accent"
      onClick={onClick}
    >
      {link.icon}
      {open ? <span className="whitespace-pre text-base text-foreground">{link.label}</span> : null}
    </Link>
  );
}

export function getSidebarLinks(pathname: string | null, showExamPrep: boolean): SidebarLinkItem[] {
  const links: SidebarLinkItem[] = [
    {
      label: 'Обзор',
      href: '/dashboard',
      icon: (
        <IconLayoutDashboard
          className={cn('h-6 w-6 shrink-0', pathname === '/dashboard' ? 'text-primary' : 'text-muted-foreground')}
        />
      ),
    },
    {
      label: 'Лабораторные',
      href: '/dashboard/labs',
      icon: (
        <IconFlask
          className={cn(
            'h-6 w-6 shrink-0',
            pathname?.startsWith('/dashboard/labs') ? 'text-primary' : 'text-muted-foreground',
          )}
        />
      ),
    },
  ];

  if (showExamPrep) {
    links.push({
      label: 'Подготовка',
      href: '/dashboard/exam-prep',
      icon: (
        <BookOpenText
          className={cn(
            'h-6 w-6 shrink-0',
            pathname?.startsWith('/dashboard/exam-prep') ? 'text-primary' : 'text-muted-foreground',
          )}
        />
      ),
    });
  }

  links.push(
    {
      label: 'Посещаемость',
      href: '/dashboard/attendance',
      icon: (
        <IconCalendar
          className={cn(
            'h-6 w-6 shrink-0',
            pathname === '/dashboard/attendance' ? 'text-primary' : 'text-muted-foreground',
          )}
        />
      ),
    },
    {
      label: 'Баллы',
      href: '/dashboard/activities',
      icon: (
        <IconStar
          className={cn(
            'h-6 w-6 shrink-0',
            pathname === '/dashboard/activities' ? 'text-primary' : 'text-muted-foreground',
          )}
        />
      ),
    },
    {
      label: 'Настройки',
      href: '/dashboard/settings',
      icon: (
        <IconSettings
          className={cn(
            'h-6 w-6 shrink-0',
            pathname === '/dashboard/settings' ? 'text-primary' : 'text-muted-foreground',
          )}
        />
      ),
    },
  );

  return links;
}
