import * as React from "react"

import { cn } from "@/lib/utils"
import { Card } from "@/components/ui/card"

type MetricCardTint =
  | "neutral"
  | "cyan"
  | "blue"
  | "green"
  | "yellow"
  | "orange"
  | "purple"
  | "red"

const TINT_STYLES: Record<MetricCardTint, { glow: string; line: string }> = {
  neutral: {
    glow: "bg-transparent",
    line: "via-border/60",
  },
  cyan: {
    glow: "bg-cyan-500/15",
    line: "via-cyan-500/35",
  },
  blue: {
    glow: "bg-blue-500/15",
    line: "via-blue-500/35",
  },
  green: {
    glow: "bg-green-500/15",
    line: "via-green-500/35",
  },
  yellow: {
    glow: "bg-yellow-500/15",
    line: "via-yellow-500/35",
  },
  orange: {
    glow: "bg-orange-500/15",
    line: "via-orange-500/35",
  },
  purple: {
    glow: "bg-purple-500/15",
    line: "via-purple-500/35",
  },
  red: {
    glow: "bg-red-500/15",
    line: "via-red-500/35",
  },
}

interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  tint?: MetricCardTint
  interactive?: boolean
}

export function MetricCard({
  className,
  children,
  tint = "neutral",
  interactive = true,
  ...props
}: MetricCardProps) {
  const tintStyle = TINT_STYLES[tint]

  return (
    <Card
      className={cn(
        "group relative overflow-hidden rounded-3xl border-border/60 bg-card/95 shadow-sm",
        interactive && "transition-all duration-200 hover:-translate-y-0.5 hover:border-border hover:shadow-lg",
        className
      )}
      {...props}
    >
      <div className={cn("pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent to-transparent", tintStyle.line)} />
      <div className={cn("pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full blur-3xl", tintStyle.glow)} />
      <div className="relative">{children}</div>
    </Card>
  )
}
