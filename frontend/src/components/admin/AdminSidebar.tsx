"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { 
  Menu,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { AdminSidebarNav } from "./AdminSidebarNav";
import { useAdminFeedbackCount } from "./useAdminFeedbackCount";

interface NavContentProps {
  pathname: string;
  onClose?: () => void;
  isCollapsed?: boolean;
  feedbackCount: number;
}

function NavContent({ pathname, onClose, isCollapsed, feedbackCount }: NavContentProps) {
  return (
    <AdminSidebarNav
      pathname={pathname}
      onClose={onClose}
      isCollapsed={isCollapsed}
      feedbackCount={feedbackCount}
    />
  );
}

export function AdminSidebar() {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = React.useState(false);
  const feedbackCount = useAdminFeedbackCount();

  return (
    <>
      {/* Desktop: боковая панель */}
      <aside className={cn(
        "hidden lg:flex h-screen flex-col sticky left-0 top-0 z-40 border-r border-border backdrop-blur-xl bg-background/40 transition-all duration-300",
        isCollapsed ? "w-16" : "w-72"
      )}>
        <NavContent pathname={pathname} isCollapsed={isCollapsed} feedbackCount={feedbackCount} />
        <Button
          variant="ghost"
          size="icon"
          className="absolute -right-3 top-1/2 -translate-y-1/2 h-6 w-6 rounded-full border border-border bg-background z-50"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
        </Button>
      </aside>
    </>
  );
}

interface MobileSidebarTriggerProps {
  className?: string;
}

function MobileSidebarTrigger({ className }: MobileSidebarTriggerProps) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = React.useState(false);
  const feedbackCount = useAdminFeedbackCount();

  return (
    <div className={cn("lg:hidden", className)}>
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="relative">
            <Menu className="h-5 w-5" />
            {feedbackCount > 0 && <span className="absolute -top-1 -right-1 h-2.5 w-2.5 bg-destructive rounded-full" />}
            <span className="sr-only">Открыть меню</span>
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-72 p-0 backdrop-blur-xl bg-background/95 border-r border-border">
          <SheetHeader className="sr-only">
            <SheetTitle>Навигация администратора</SheetTitle>
            <SheetDescription>Основные разделы и быстрые переходы по административным страницам.</SheetDescription>
          </SheetHeader>
          <NavContent pathname={pathname} onClose={() => setIsOpen(false)} feedbackCount={feedbackCount} />
        </SheetContent>
      </Sheet>
    </div>
  );
}

export { MobileSidebarTrigger };
