"use client";
import React, { useEffect, useMemo, useState } from "react";
import {
  IconLogout,
  IconMenu2,
  IconX,
} from "@tabler/icons-react";
import { motion, AnimatePresence } from "motion/react";
import { useRouter, usePathname } from "next/navigation";
import { AnimatedThemeToggler } from "@/components/ui/animated-theme-toggler";
import { NotificationBell } from "./NotificationBell";
import { SidebarLogo, SidebarLogoIcon } from "./sidebar-brand";
import { getSidebarLinks, NavLink } from "./sidebar-links";
import api from "@/lib/api";
import { StudentAPI } from "@/lib/api/student";

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
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [hasExamPrep, setHasExamPrep] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadExamPrepOfferings = async () => {
      try {
        const offerings = await StudentAPI.getExamPrepOfferings();
        if (!cancelled) {
          setHasExamPrep(offerings.length > 0);
        }
      } catch {
        // Keep the link visible on transient failures so the feature does not disappear from navigation.
      }
    };

    void loadExamPrepOfferings();

    return () => {
      cancelled = true;
    };
  }, []);

  // Close mobile menu on navigation
  const handleLinkClick = () => {
    setOpen(false);
  };

  const links = useMemo(
    () => getSidebarLinks(pathname, hasExamPrep !== false || pathname?.startsWith("/dashboard/exam-prep") === true),
    [hasExamPrep, pathname],
  );

  const handleLogout = async () => {
    console.log('[Component:AceternitySidebar] Logout initiated');
    try {
      await api.post('/auth/logout');
    } catch {
      // ignore
    }
    // Очищаем store
    const { useAuthStore } = await import('@/stores');
    useAuthStore.getState().logout();
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
    <div className="min-h-dvh w-full flex flex-col md:flex-row bg-background">
      {/* Desktop Sidebar - only on md+ */}
      <aside 
        className="hidden md:flex md:flex-col shrink-0 border-r border-border bg-background h-dvh sticky top-0 transition-all duration-200"
        style={{ width: open ? 300 : 70 }}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => !popoverOpen && setOpen(false)}
      >
        <div className="flex flex-col h-full justify-between px-4 py-4">
          <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
            {open ? <SidebarLogo /> : <SidebarLogoIcon />}
            <div className="mt-8 flex flex-col gap-1">
              {links.map((link, idx) => (
                <NavLink key={idx} link={link} open={open} onClick={handleLinkClick} />
              ))}
            </div>
          </div>
          
          {/* Logout */}
          <div className="border-t border-border pt-4 mt-4">
            <div className="flex items-center justify-center gap-2 px-2 mb-2">
              <NotificationBell onOpenChange={setPopoverOpen} />
              <AnimatedThemeToggler />
            </div>
            
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 py-2.5 px-2 rounded-lg hover:bg-destructive/10 transition-colors w-full text-left"
            >
              <IconLogout className="h-6 w-6 shrink-0 text-destructive" />
              {open && (
                <span className="text-destructive text-base whitespace-pre">
                  Выйти
                </span>
              )}
            </button>
          </div>

          {/* User */}
          <div className="mt-4 flex items-center gap-3 px-2 py-2">
            <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <span className="text-sm font-medium text-primary">{initials}</span>
            </div>
            {open && (
              <div className="flex flex-col overflow-hidden">
                <span className="text-sm font-medium text-foreground truncate">
                  {user.name}
                </span>
                <span className="text-xs text-muted-foreground truncate">
                  {user.group || `@${user.username}` || "Студент"}
                </span>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Mobile Header - only on mobile */}
      <header className="md:hidden flex items-center justify-between h-14 px-4 border-b border-border bg-background shrink-0 sticky top-0 z-50">
        <button
          onClick={() => setOpen(!open)}
          className="p-2 -ml-2 rounded-lg hover:bg-accent"
        >
          <IconMenu2 className="h-6 w-6 text-foreground" />
        </button>
        <SidebarLogoIcon />
        <div className="w-10" /> {/* Spacer for centering */}
      </header>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="md:hidden fixed inset-0 bg-black/50 z-[100]"
              onClick={() => setOpen(false)}
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="md:hidden fixed top-0 left-0 h-dvh w-[280px] max-w-[85vw] bg-background z-[101] flex flex-col border-r border-border shadow-xl"
            >
              <div className="flex items-center justify-between p-4 border-b border-border">
                <SidebarLogo />
                <button
                  onClick={() => setOpen(false)}
                  className="p-2 rounded-lg hover:bg-accent"
                >
                  <IconX className="h-5 w-5 text-foreground" />
                </button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4">
                <div className="flex flex-col gap-1">
                  {links.map((link, idx) => (
                    <NavLink key={idx} link={link} open={true} onClick={handleLinkClick} />
                  ))}
                </div>
              </div>

              <div className="border-t border-border p-4">
                <div className="flex items-center justify-center gap-2 mb-4">
                  <NotificationBell onOpenChange={setPopoverOpen} />
                  <AnimatedThemeToggler />
                </div>
                
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-3 py-2.5 px-2 rounded-lg hover:bg-destructive/10 transition-colors w-full text-left"
                >
                  <IconLogout className="h-6 w-6 shrink-0 text-destructive" />
                  <span className="text-destructive text-base">Выйти</span>
                </button>

                <div className="mt-4 flex items-center gap-3 px-2 py-2">
                  <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <span className="text-sm font-medium text-primary">{initials}</span>
                  </div>
                  <div className="flex flex-col overflow-hidden">
                    <span className="text-sm font-medium text-foreground truncate">
                      {user.name}
                    </span>
                    <span className="text-xs text-muted-foreground truncate">
                      {user.group || `@${user.username}` || "Студент"}
                    </span>
                  </div>
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
      
      {/* Main Content */}
      <main className="flex-1 overflow-auto w-full">
        {children}
      </main>
    </div>
  );
}
