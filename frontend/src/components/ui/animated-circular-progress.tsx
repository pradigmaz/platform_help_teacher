"use client";

import { motion } from "motion/react";
import { cn } from "@/lib/utils";
import { useId } from "react";

interface AnimatedCircularProgressProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
  gradientFrom?: string;
  gradientTo?: string;
  showValue?: boolean;
  label?: string;
  children?: React.ReactNode;
}

export function AnimatedCircularProgress({
  value,
  max = 100,
  size = 120,
  strokeWidth = 10,
  className,
  gradientFrom = "#22c55e",
  gradientTo = "#10b981",
  showValue = true,
  label,
  children,
}: AnimatedCircularProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const percent = Math.min((value / max) * 100, 100);
  const offset = circumference - (percent / 100) * circumference;
  const gradientId = useId();

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={gradientFrom} />
            <stop offset="100%" stopColor={gradientTo} />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-muted/20"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          style={{ strokeDasharray: circumference }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {children ? (
          children
        ) : (
          <>
            {showValue && (
              <motion.span
                className="text-2xl font-bold"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5, duration: 0.5 }}
              >
                {Math.round(percent)}%
              </motion.span>
            )}
            {label && (
              <span className="text-xs text-muted-foreground mt-1">{label}</span>
            )}
          </>
        )}
      </div>
    </div>
  );
}
