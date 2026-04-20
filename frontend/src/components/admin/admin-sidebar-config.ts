"use client";

import type * as React from "react";
import {
  Award,
  BarChart3,
  BookOpenCheck,
  BookOpen,
  Calendar,
  ClipboardList,
  FlaskConical,
  GraduationCap,
  LayoutDashboard,
  Megaphone,
  MessageSquare,
  NotebookTabs,
  Settings,
  Shield,
} from "lucide-react";

export interface SidebarSubItem {
  title: string;
  href: string;
  icon: React.ElementType;
}

export interface SidebarItem {
  title: string;
  href: string;
  icon: React.ElementType;
  subItems?: SidebarSubItem[];
  badge?: "feedback";
}

interface AdminSidebarItemsOptions {
  hasExams: boolean;
}

export function getAdminSidebarItems({ hasExams }: AdminSidebarItemsOptions): SidebarItem[] {
  return [
    { title: "Дашборд", href: "/admin", icon: LayoutDashboard },
    { title: "Группы", href: "/admin/groups", icon: GraduationCap },
    {
      title: "Курс",
      href: "/admin/course",
      icon: BookOpenCheck,
      subItems: [
        { title: "Лекции", href: "/admin/lectures", icon: BookOpen },
        { title: "Лабораторные", href: "/admin/labs", icon: FlaskConical },
        ...(hasExams ? [{ title: "Экзамены", href: "/admin/exams", icon: BookOpenCheck }] : []),
      ],
    },
    { title: "Предметы групп", href: "/admin/subjects", icon: NotebookTabs },
    {
      title: "Аттестация",
      href: "/admin/attestation",
      icon: Award,
      subItems: [
        { title: "Баллы", href: "/admin/attestation/scores", icon: BarChart3 },
        { title: "Настройки", href: "/admin/attestation", icon: Settings },
      ],
    },
    { title: "Расписание", href: "/admin/schedule", icon: Calendar },
    { title: "Журнал", href: "/admin/journal", icon: ClipboardList },
    { title: "Аудит", href: "/admin/audit", icon: Shield },
    { title: "Объявления", href: "/admin/announcements", icon: Megaphone },
    { title: "Обращения", href: "/admin/feedback", icon: MessageSquare, badge: "feedback" },
    { title: "Настройки", href: "/admin/settings", icon: Settings },
  ];
}
