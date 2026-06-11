import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-9 w-full rounded-md border border-border bg-panel2 px-3 text-sm text-ink outline-none placeholder:text-muted focus:border-amber/60",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";
