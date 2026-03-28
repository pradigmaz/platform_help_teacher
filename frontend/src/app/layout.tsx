import type { Metadata } from "next";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

function getFingerprintMode(): 'off' | 'auth_only' {
  const value = (
    process.env.FRONTEND_FINGERPRINT_MODE
    ?? process.env.FINGERPRINT_MODE
    ?? process.env.NEXT_PUBLIC_FINGERPRINT_MODE
    ?? 'off'
  )
    .trim()
    .toLowerCase();

  return value === 'auth_only' ? 'auth_only' : 'off';
}

export const metadata: Metadata = {
  title: "Edu Platform",
  description: "Next Gen Education",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" suppressHydrationWarning data-fingerprint-mode={getFingerprintMode()}>
      <body className="min-h-screen bg-background font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
