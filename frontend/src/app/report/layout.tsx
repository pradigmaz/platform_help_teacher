'use client';

import { ThemeProvider } from '@/components/theme-provider';
import { Toaster } from '@/components/ui/sonner';
import { AnimatedThemeToggler } from '@/components/ui/animated-theme-toggler';

export default function ReportLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <div className="min-h-screen bg-background">
        {/* Theme toggle in top right */}
        <div className="fixed top-4 right-4 z-50">
          <AnimatedThemeToggler />
        </div>
        <main className="container mx-auto px-4 py-8 max-w-6xl">
          {children}
        </main>
      </div>
      <Toaster />
    </ThemeProvider>
  );
}
