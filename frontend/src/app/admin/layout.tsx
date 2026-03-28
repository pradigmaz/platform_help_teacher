"use client";

import * as React from "react";
import { useRouter, usePathname } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AdminSidebar, MobileSidebarTrigger } from "@/components/admin/AdminSidebar";
import { AdminSessionProvider, useAdminSession } from "@/components/admin/AdminSessionProvider";
import { OnboardingDialog } from "@/components/admin/OnboardingDialog";
import { DotPattern } from "@/components/ui/dot-pattern";
import { BlurFade } from "@/components/ui/blur-fade";
import { cn } from "@/lib/utils";
import { AnimatedThemeToggler } from "@/components/ui/animated-theme-toggler";
import { toast } from "@/components/ui/sonner";
import { ApiErrorBoundary } from "@/components/ui/api-error-boundary";

function AdminLayoutContent({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, refetch } = useAdminSession();
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
        <header className="h-14 lg:h-16 border-b border-border flex items-center justify-between px-4 lg:px-8 gap-4 bg-background/40 backdrop-blur-xl sticky top-0 z-30">
          <MobileSidebarTrigger />
          <div className="flex-1" />
          <AnimatedThemeToggler />
        </header>
        <main className="flex-1 transition-all duration-300 overflow-y-auto">
          <BlurFade delay={0.1} duration={0.5}>
            <div className="container mx-auto p-4 lg:p-8">
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

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminSessionProvider>
      <AdminLayoutContent>{children}</AdminLayoutContent>
    </AdminSessionProvider>
  );
}
