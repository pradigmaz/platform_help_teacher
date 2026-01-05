"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { cn } from "@/lib/utils";

interface SparkleProps {
  id: string;
  createdAt: number;
  color: string;
  size: number;
  style: {
    top: string;
    left: string;
  };
}

const generateSparkle = (color: string): SparkleProps => {
  return {
    id: String(Math.random()),
    createdAt: Date.now(),
    color,
    size: Math.random() * 10 + 5,
    style: {
      top: Math.random() * 100 + "%",
      left: Math.random() * 100 + "%",
    },
  };
};

const Sparkle = ({ color, size, style }: Omit<SparkleProps, "id" | "createdAt">) => {
  return (
    <motion.svg
      initial={{ scale: 0, rotate: 0 }}
      animate={{ scale: 1, rotate: 180 }}
      exit={{ scale: 0 }}
      width={size}
      height={size}
      viewBox="0 0 160 160"
      fill="none"
      style={{
        position: "absolute",
        pointerEvents: "none",
        ...style,
      }}
    >
      <path
        d="M80 0C80 0 84.2846 41.2925 101.496 58.504C118.707 75.7154 160 80 160 80C160 80 118.707 84.2846 101.496 101.496C84.2846 118.707 80 160 80 160C80 160 75.7154 118.707 58.504 101.496C41.2925 84.2846 0 80 0 80C0 80 41.2925 75.7154 58.504 58.504C75.7154 41.2925 80 0 80 0Z"
        fill={color}
      />
    </motion.svg>
  );
};

interface SparklesProps {
  children: React.ReactNode;
  className?: string;
  color?: string;
}

export function Sparkles({ children, className, color = "#FFC700" }: SparklesProps) {
  const [sparkles, setSparkles] = useState<SparkleProps[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const sparkle = generateSparkle(color);
      setSparkles((s) => [...s.filter((sp) => now - sp.createdAt < 750), sparkle]);
    }, 400);

    return () => clearInterval(interval);
  }, [color]);

  return (
    <span className={cn("relative inline-block", className)}>
      <AnimatePresence>
        {sparkles.map((sparkle) => (
          <Sparkle
            key={sparkle.id}
            color={sparkle.color}
            size={sparkle.size}
            style={sparkle.style}
          />
        ))}
      </AnimatePresence>
      <span className="relative z-10">{children}</span>
    </span>
  );
}
