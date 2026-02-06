import * as React from "react"

const MOBILE_BREAKPOINT = 768

/**
 * Hook для определения мобильного устройства.
 * Возвращает undefined до hydration, затем true/false.
 * Это предотвращает hydration mismatch между сервером и клиентом.
 */
export function useIsMobile(): boolean | undefined {
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(undefined)

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }
    mql.addEventListener("change", onChange)
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  return isMobile
}
