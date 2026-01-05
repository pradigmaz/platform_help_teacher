"use client";
import React, { useState } from "react";
import { Sidebar, SidebarBody, SidebarLink } from "@/components/ui/aceternity-sidebar";
import {
  IconLayoutDashboard,
  IconFlask,
  IconCalendar,
  IconSettings,
  IconLogout,
  IconSchool,
} from "@tabler/icons-react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";
import { useRouter, usePathname } from "next/navigation";
import { AnimatedThemeToggler } from "@/components/ui/animated-theme-toggler";

interface AceternitySidebarProps {
  children: React.ReactNode;
  user: {
    name: string;
    username?: string;
    group?: string;
  };
}

export function AceternitySidebarLayout({ children, user }: AceternitySidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const links = [
    {
      label: "Обзор",
      href: "/dashboard",
      icon: (
        <IconLayoutDashboard className={cn(
          "h-6 w-6 shrink-0",
          pathname === "/dashboard" ? "text-primary" : "text-neutral-700 dark:text-neutral-200"
        )} />
      ),
    },
    {
      label: "Лабораторные",
      href: "/dashboard/labs",
      icon: (
        <IconFlask className={cn(
          "h-6 w-6 shrink-0",
          pathname === "/dashboard/labs" ? "text-primary" : "text-neutral-700 dark:text-neutral-200"
        )} />
      ),
    },
    {
      label: "Посещаемость",
      href: "/dashboard/attendance",
      icon: (
        <IconCalendar className={cn(
          "h-6 w-6 shrink-0",
          pathname === "/dashboard/attendance" ? "text-primary" : "text-neutral-700 dark:text-neutral-200"
        )} />
      ),
    },
    {
      label: "Настройки",
      href: "/dashboard/settings",
      icon: (
        <IconSettings className={cn(
          "h-6 w-6 shrink-0",
          pathname === "/dashboard/settings" ? "text-primary" : "text-neutral-700 dark:text-neutral-200"
        )} />
      ),
    },
  ];

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  const initials = user.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-background">
      <Sidebar open={open} setOpen={setOpen}>
        <SidebarBody className="flex flex-col h-full justify-between border-r border-border">
          <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
            {open ? <Logo /> : <LogoIcon />}
            <div className="mt-8 flex flex-col gap-1">
              {links.map((link, idx) => (
                <SidebarLink key={idx} link={link} />
              ))}
            </div>
          </div>
          
          {/* Logout */}
          <div className="border-t border-border pt-4 mt-4">
            <div className="flex items-center justify-between px-2 mb-2">
              <AnimatedThemeToggler />
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 py-2.5 px-2 rounded-lg hover:bg-destructive/10 transition-colors w-full text-left"
            >
              <IconLogout className="h-6 w-6 shrink-0 text-destructive" />
              <motion.span
                animate={{
                  display: open ? "inline-block" : "none",
                  opacity: open ? 1 : 0,
                }}
                className="text-destructive text-base whitespace-pre"
              >
                Выйти
              </motion.span>
            </button>
          </div>

          {/* User */}
          <div className="mt-4 flex items-center gap-3 px-2 py-2">
            <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <span className="text-sm font-medium text-primary">{initials}</span>
            </div>
            {open && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col overflow-hidden"
              >
                <span className="text-sm font-medium text-foreground truncate">
                  {user.name}
                </span>
                <span className="text-xs text-muted-foreground truncate">
                  {user.group || `@${user.username}` || "Студент"}
                </span>
              </motion.div>
            )}
          </div>
        </SidebarBody>
      </Sidebar>
      
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}

const Logo = () => {
  return (
    <a
      href="/dashboard"
      className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal"
    >
      <div className="h-7 w-7 shrink-0 rounded-lg bg-primary flex items-center justify-center">
        <IconSchool className="h-5 w-5 text-primary-foreground" />
      </div>
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="font-semibold whitespace-pre text-foreground text-lg"
      >
        Студент
      </motion.span>
    </a>
  );
};

const LogoIcon = () => {
  return (
    <a
      href="/dashboard"
      className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal"
    >
      <div className="h-7 w-7 shrink-0 rounded-lg bg-primary flex items-center justify-center">
        <IconSchool className="h-5 w-5 text-primary-foreground" />
      </div>
    </a>
  );
};
