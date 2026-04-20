'use client';

import { IconSchool } from '@tabler/icons-react';
import { motion } from 'motion/react';

export function SidebarLogo() {
  return (
    <a
      href="/dashboard"
      className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal"
    >
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary">
        <IconSchool className="h-5 w-5 text-primary-foreground" />
      </div>
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="whitespace-pre text-lg font-semibold text-foreground"
      >
        Студент
      </motion.span>
    </a>
  );
}

export function SidebarLogoIcon() {
  return (
    <a
      href="/dashboard"
      className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal"
    >
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary">
        <IconSchool className="h-5 w-5 text-primary-foreground" />
      </div>
    </a>
  );
}
