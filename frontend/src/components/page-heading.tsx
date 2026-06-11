import { ReactNode } from "react";

export function PageHeading({
  eyebrow,
  title,
  children
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <div className="text-xs font-medium uppercase text-amber">{eyebrow}</div>
        <h1 className="mt-1 text-2xl font-semibold tracking-normal text-ink md:text-3xl">{title}</h1>
      </div>
      {children}
    </div>
  );
}
