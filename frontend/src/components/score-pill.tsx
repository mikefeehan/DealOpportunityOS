import { cn } from "@/lib/utils";

export function ScorePill({ value, label, className }: { value: number; label?: string; className?: string }) {
  const tone = value >= 78 ? "text-green border-green/40 bg-green/10" : value >= 58 ? "text-amber border-amber/40 bg-amber/10" : "text-muted border-border bg-panel2";
  return (
    <span className={cn("inline-flex min-w-16 items-center justify-center rounded-md border px-2 py-1 text-sm font-semibold", tone, className)}>
      {label ? `${label} ` : ""}
      {value.toFixed(1)}
    </span>
  );
}
