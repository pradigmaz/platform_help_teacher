"use client";

import * as React from "react";
import { useRouter, usePathname } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { OnboardingDialog } from "@/components/admin/OnboardingDialog";
import { DotPattern } from "@/components/ui/dot-pattern";
import { BlurFade } from "@/components/ui/blur-fade";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/theme-toggle";
import { AnimatedThemeToggler } from "@/components/ui/animated-theme-toggler";
import { toast } from "@/components/ui/sonner";
import { ApiErrorBoundary } from "@/components/ui/api-error-boundary";

// Mock useAuth hook as requested
interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "teacher" | "student";
  onboarding_completed: boolean;
}

function useAuth() {
  const [user, setUser] = React.useState<User | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  const refetch = React.useCallback(async () => {
    try {
      const res = await fetch('/api/v1/users/me', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setUser({ 
          id: data.id, 
          email: data.username || data.full_name, 
          full_name: data.full_name,
          role: data.role,
          onboarding_completed: data.onboarding_completed 
        });
      }
    } catch (err) {
      console.error('Auth check failed:', err);
    }
  }, []);

  React.useEffect(() => {
    const checkAuth = async () => {
      await refetch();
      setIsLoading(false);
    };
    checkAuth();
  }, [refetch]);

  return { user, isLoading, refetch };
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, refetch } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [showFioDialog, setShowFioDialog] = React.useState(false);

  // Проверка onboarding после загрузки
  React.useEffect(() => {
    if (!isLoading && user) {
      if (!user.onboarding_completed && pathname !== '/admin/attestation') {
        setShowFioDialog(true);
      }
    }
  }, [isLoading, user, pathname]);

  // Refetch при смене pathname (после редиректа с аттестации)
  React.useEffect(() => {
    if (!isLoading && pathname !== '/admin/attestation') {
      refetch();
    }
  }, [pathname, isLoading, refetch]);

  const handleFioComplete = async () => {
    setShowFioDialog(false);
    await refetch();
    toast.success('Настройка завершена');
    router.push('/admin');
  };

  React.useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.push("/auth/login");
      } else if (user.role === "student") {
        router.push("/dashboard");
      }
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user || user.role === "student") {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground relative">
      <OnboardingDialog open={showFioDialog} onComplete={handleFioComplete} />
      <DotPattern
        className={cn(
          "[mask-image:radial-gradient(800px_circle_at_center,white,transparent)]",
          "opacity-40 dark:opacity-20 fixed inset-0"
        )}
      />
      <AdminSidebar />
      <div className="flex-1 flex flex-col relative z-10 transition-all duration-300 min-h-screen">
        <header className="h-16 border-b border-border flex items-center justify-end px-8 gap-4 bg-background/40 backdrop-blur-xl sticky top-0 z-30">
          <AnimatedThemeToggler />
        </header>
        <main className="flex-1 transition-all duration-300 overflow-y-auto">
          <BlurFade delay={0.1} duration={0.5}>
            <div className="container mx-auto p-6 lg:p-8">
              <ApiErrorBoundary>
                {children}
              </ApiErrorBoundary>
            </div>
          </BlurFade>
        </main>
      </div>
    </div>
  );
}
