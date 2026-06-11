import * as React from "react";
import { cn } from "@/lib/utils";

type BadgeTone = "default" | "green" | "amber" | "red" | "cyan";

const toneClass: Record<BadgeTone, string> = {
  default: "border-border bg-panel2 text-muted",
  green: "border-green/35 bg-green/10 text-green",
  amber: "border-amber/35 bg-amber/10 text-amber",
  red: "border-red/35 bg-red/10 text-red",
  cyan: "border-cyan/35 bg-cyan/10 text-cyan"
};

export function Badge({
  className,
  tone = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: BadgeTone }) {
  return (
    <span
      className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium", toneClass[tone], className)}
      {...props}
    />
  );
}
