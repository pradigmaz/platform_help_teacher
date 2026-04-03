"use client";

import * as React from "react";
import Link from "next/link";
import { ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { HoverBorderGradient } from "@/components/ui/hover-border-gradient";
import { cn } from "@/lib/utils";
import { adminSidebarItems } from "./admin-sidebar-config";

interface AdminSidebarNavProps {
  pathname: string;
  feedbackCount: number;
  isCollapsed?: boolean;
  onClose?: () => void;
}

function FeedbackBadge({ count }: { count: number }) {
  if (count <= 0) {
    return null;
  }

  return (
    <Badge variant="destructive" className="h-5 min-w-5 px-1.5 text-xs">
      {count}
    </Badge>
  );
}

function SidebarIcon({
  icon: Icon,
  showDot,
}: {
  icon: React.ElementType;
  showDot: boolean;
}) {
  return (
    <div className="relative">
      <Icon className="h-4 w-4 shrink-0" />
      {showDot && <span className="absolute -top-1.5 -right-1.5 h-2 w-2 bg-destructive rounded-full" />}
    </div>
  );
}

export function AdminSidebarNav({
  pathname,
  feedbackCount,
  isCollapsed,
  onClose,
}: AdminSidebarNavProps) {
  const [openSubmenus, setOpenSubmenus] = React.useState<string[]>(() =>
    adminSidebarItems.flatMap((item) =>
      item.subItems?.some((subItem) => pathname === subItem.href || pathname.startsWith(`${subItem.href}/`))
        ? [item.href]
        : []
    )
  );

  const toggleSubmenu = (href: string) => {
    setOpenSubmenus((current) =>
      current.includes(href) ? current.filter((item) => item !== href) : [...current, href]
    );
  };

  const getBadgeCount = (badge?: string) => (badge === "feedback" ? feedbackCount : 0);

  return (
    <div className="flex flex-col h-full py-4 overflow-hidden">
      <div className={cn("px-4 mb-8 transition-all duration-300 shrink-0", isCollapsed ? "opacity-0" : "opacity-100")}>
        {!isCollapsed && <h2 className="text-xl font-bold tracking-tight text-foreground">Панель управления</h2>}
      </div>
      <nav className="flex-1 px-2 overflow-y-auto">
        <div className="space-y-2">
          {adminSidebarItems.map((item) => {
            const isActive = pathname === item.href;
            const hasSubItems = Boolean(item.subItems?.length);
            const isSubItemActive = item.subItems?.some(
              (subItem) => pathname === subItem.href || pathname.startsWith(`${subItem.href}/`)
            );
            const isSubmenuOpen = openSubmenus.includes(item.href);
            const badgeCount = getBadgeCount(item.badge);

            if (hasSubItems && !isCollapsed) {
              return (
                <Collapsible key={item.href} open={isSubmenuOpen} onOpenChange={() => toggleSubmenu(item.href)}>
                  <CollapsibleTrigger asChild>
                    <button
                      className={cn(
                        "w-full flex items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-accent",
                        isSubItemActive ? "text-foreground bg-accent/50" : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <item.icon className="h-4 w-4 shrink-0" />
                        <span>{item.title}</span>
                      </div>
                      <ChevronDown className={cn("h-4 w-4 shrink-0 transition-transform duration-200", isSubmenuOpen && "rotate-180")} />
                    </button>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="pl-4 mt-1 space-y-1">
                    {item.subItems?.map((subItem) => {
                      const isSubActive = pathname === subItem.href;
                      return (
                        <Link key={subItem.href} href={subItem.href} onClick={onClose} className="block">
                          {isSubActive ? (
                            <HoverBorderGradient
                              containerClassName="w-full rounded-lg"
                              className="w-full flex items-center gap-3 bg-background text-foreground px-3 py-2 text-sm font-medium"
                              duration={1}
                            >
                              <subItem.icon className="h-4 w-4 shrink-0" />
                              <span>{subItem.title}</span>
                            </HoverBorderGradient>
                          ) : (
                            <div className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-accent text-muted-foreground hover:text-foreground">
                              <subItem.icon className="h-4 w-4 shrink-0" />
                              <span>{subItem.title}</span>
                            </div>
                          )}
                        </Link>
                      );
                    })}
                  </CollapsibleContent>
                </Collapsible>
              );
            }

            return (
              <Link
                key={item.href}
                href={hasSubItems ? (item.subItems?.[0]?.href || item.href) : item.href}
                onClick={onClose}
                className="block"
              >
                {isActive || (hasSubItems && isSubItemActive) ? (
                  <HoverBorderGradient
                    containerClassName="w-full rounded-lg"
                    className="w-full flex items-center gap-3 bg-background text-foreground px-3 py-2 text-sm font-medium"
                    duration={1}
                  >
                    <SidebarIcon icon={item.icon} showDot={false} />
                    {!isCollapsed && <span className="flex-1">{item.title}</span>}
                    {!isCollapsed && <FeedbackBadge count={badgeCount} />}
                  </HoverBorderGradient>
                ) : (
                  <div
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-accent text-muted-foreground hover:text-foreground",
                      isCollapsed && "justify-center px-0"
                    )}
                  >
                    <SidebarIcon icon={item.icon} showDot={Boolean(isCollapsed && badgeCount > 0)} />
                    {!isCollapsed && <span className="flex-1">{item.title}</span>}
                    {!isCollapsed && <FeedbackBadge count={badgeCount} />}
                  </div>
                )}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
