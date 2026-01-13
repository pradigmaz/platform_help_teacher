"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  BookOpen, 
  FlaskConical, 
  Menu,
  LayoutDashboard,
  ChevronLeft,
  ChevronRight,
  GraduationCap,
  Calendar,
  ClipboardList,
  Award,
  Settings,
  BarChart3,
  ChevronDown,
  Shield,
  MessageSquare
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { HoverBorderGradient } from "@/components/ui/hover-border-gradient";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";

// Hook для получения количества новых фидбэков
function useNewFeedbackCount() {
  const [count, setCount] = React.useState(0);

  React.useEffect(() => {
    const fetchCount = async () => {
      try {
        const { data } = await api.get('/feedback/count/new');
        setCount(data.count);
      } catch {
        // Ignore - user might not be admin
      }
    };

    fetchCount();
    const interval = setInterval(fetchCount, 60000);
    return () => clearInterval(interval);
  }, []);

  return count;
}

interface SidebarSubItem {
  title: string;
  href: string;
  icon: React.ElementType;
}

interface SidebarItem {
  title: string;
  href: string;
  icon: React.ElementType;
  subItems?: SidebarSubItem[];
  badge?: 'feedback';
}

const sidebarItems: SidebarItem[] = [
  { title: "Дашборд", href: "/admin", icon: LayoutDashboard },
  { title: "Группы", href: "/admin/groups", icon: GraduationCap },
  { title: "Лекции", href: "/admin/lectures", icon: BookOpen },
  { title: "Лабораторные", href: "/admin/labs", icon: FlaskConical },
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
  { title: "Обращения", href: "/admin/feedback", icon: MessageSquare, badge: 'feedback' },
  { title: "Настройки", href: "/admin/settings", icon: Settings },
];

interface NavContentProps {
  pathname: string;
  onClose?: () => void;
  isCollapsed?: boolean;
  feedbackCount: number;
}

function NavContent({ pathname, onClose, isCollapsed, feedbackCount }: NavContentProps) {
  const [openSubmenus, setOpenSubmenus] = React.useState<string[]>(() => {
    const openItems: string[] = [];
    sidebarItems.forEach(item => {
      if (item.subItems?.some(sub => pathname === sub.href || pathname.startsWith(sub.href + '/'))) {
        openItems.push(item.href);
      }
    });
    return openItems;
  });

  const toggleSubmenu = (href: string) => {
    setOpenSubmenus(prev => 
      prev.includes(href) ? prev.filter(h => h !== href) : [...prev, href]
    );
  };

  const getBadgeCount = (badge?: string) => {
    if (badge === 'feedback') return feedbackCount;
    return 0;
  };

  return (
    <div className="flex flex-col h-full py-4 overflow-hidden">
      <div className={cn("px-4 mb-8 transition-all duration-300 shrink-0", isCollapsed ? "opacity-0" : "opacity-100")}>
        {!isCollapsed && <h2 className="text-xl font-bold tracking-tight text-foreground">Панель управления</h2>}
      </div>
      <nav className="flex-1 px-2 overflow-y-auto">
        <div className="space-y-2">
          {sidebarItems.map((item) => {
            const isActive = pathname === item.href;
            const hasSubItems = item.subItems && item.subItems.length > 0;
            const isSubItemActive = item.subItems?.some(sub => pathname === sub.href || pathname.startsWith(sub.href + '/'));
            const isSubmenuOpen = openSubmenus.includes(item.href);
            const badgeCount = getBadgeCount(item.badge);

            if (hasSubItems && !isCollapsed) {
              return (
                <Collapsible key={item.href} open={isSubmenuOpen} onOpenChange={() => toggleSubmenu(item.href)}>
                  <CollapsibleTrigger asChild>
                    <button className={cn(
                      "w-full flex items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-accent",
                      isSubItemActive ? "text-foreground bg-accent/50" : "text-muted-foreground hover:text-foreground"
                    )}>
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
                            <HoverBorderGradient containerClassName="w-full rounded-lg" className="w-full flex items-center gap-3 bg-background text-foreground px-3 py-2 text-sm font-medium" duration={1}>
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
              <Link key={item.href} href={hasSubItems ? (item.subItems?.[0]?.href || item.href) : item.href} onClick={onClose} className="block">
                {(isActive || (hasSubItems && isSubItemActive)) ? (
                  <HoverBorderGradient containerClassName="w-full rounded-lg" className="w-full flex items-center gap-3 bg-background text-foreground px-3 py-2 text-sm font-medium" duration={1}>
                    <item.icon className="h-4 w-4 shrink-0" />
                    {!isCollapsed && <span className="flex-1">{item.title}</span>}
                    {!isCollapsed && badgeCount > 0 && (
                      <Badge variant="destructive" className="h-5 min-w-5 px-1.5 text-xs">{badgeCount}</Badge>
                    )}
                  </HoverBorderGradient>
                ) : (
                  <div className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-accent text-muted-foreground hover:text-foreground",
                    isCollapsed && "justify-center px-0"
                  )}>
                    <div className="relative">
                      <item.icon className="h-4 w-4 shrink-0" />
                      {isCollapsed && badgeCount > 0 && (
                        <span className="absolute -top-1.5 -right-1.5 h-2 w-2 bg-destructive rounded-full" />
                      )}
                    </div>
                    {!isCollapsed && <span className="flex-1">{item.title}</span>}
                    {!isCollapsed && badgeCount > 0 && (
                      <Badge variant="destructive" className="h-5 min-w-5 px-1.5 text-xs">{badgeCount}</Badge>
                    )}
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

export function AdminSidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = React.useState(false);
  const [isCollapsed, setIsCollapsed] = React.useState(false);
  const feedbackCount = useNewFeedbackCount();

  return (
    <>
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon" className="backdrop-blur-xl bg-background/40 border-border text-foreground relative">
              <Menu className="h-5 w-5" />
              {feedbackCount > 0 && <span className="absolute -top-1 -right-1 h-2.5 w-2.5 bg-destructive rounded-full" />}
              <span className="sr-only">Открыть меню</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 p-0 backdrop-blur-xl bg-background/60 border-r border-border">
            <SheetHeader className="sr-only">
              <SheetTitle>Навигация администратора</SheetTitle>
            </SheetHeader>
            <NavContent pathname={pathname} onClose={() => setIsOpen(false)} feedbackCount={feedbackCount} />
          </SheetContent>
        </Sheet>
      </div>

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
