'use client';

export interface ToolbarGroupProps {
  label: string;
  children: React.ReactNode;
}

export function ToolbarGroup({ label, children }: ToolbarGroupProps) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <div className="flex items-center gap-0.5">
        {children}
      </div>
      <span className="text-[10px] text-muted-foreground/60 select-none">{label}</span>
    </div>
  );
}
