import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type ArchivePanelProps = {
  children: ReactNode;
  className?: string;
};

export function ArchivePanel({ children, className }: ArchivePanelProps) {
  return (
    <div className={cn("archive-panel", className)}>
      <span className="archive-panel__corner archive-panel__corner--tl" aria-hidden="true" />
      <span className="archive-panel__corner archive-panel__corner--br" aria-hidden="true" />
      {children}
    </div>
  );
}
