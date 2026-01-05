"use client"

import * as React from "react"
import { Button as BaseButton } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { getGlassStyles, type GlassCustomization } from "@/lib/glass-utils"
import { hoverEffects, type HoverEffect } from "@/lib/hover-effects"

export interface ButtonProps
  extends Omit<React.ComponentProps<typeof BaseButton>, "glass"> {
  effect?: HoverEffect
  glass?: GlassCustomization
}

/**
 * Glass UI Button - A beautifully designed button component with glassy effects
 * Built on top of the base Button component with enhanced visual effects
 * 
 * @example
 * ```tsx
 * <Button 
 *   glass={{
 *     color: "rgba(59, 130, 246, 0.2)",
 *     blur: 25,
 *     outline: "rgba(59, 130, 246, 0.4)"
 *   }}
 * >
 *   Click me
 * </Button>
 * ```
 */
export const Button = React.forwardRef<
  HTMLButtonElement,
  ButtonProps
>(({ className, effect = "glow", variant = "outline", glass, style, ...props }, ref) => {
  const glassStyles = getGlassStyles(glass)

  return (
    <BaseButton
      ref={ref}
      variant={variant as React.ComponentProps<typeof BaseButton>["variant"]}
      className={cn(
        "relative overflow-hidden",
        hoverEffects({ hover: effect }),
        className
      )}
      style={{ ...glassStyles, ...style }}
      {...props}
    />
  )
})
Button.displayName = "Button"
