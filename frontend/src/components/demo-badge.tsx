import { Badge } from "@/components/ui/badge";

// Renders a loud DEMO tag for any seeded/fallback record so a fabricated
// property or owner can never be mistaken for a real, callable lead.
export function DemoBadge({ dataStatus, className }: { dataStatus?: string; className?: string }) {
  if (dataStatus !== "seeded_fallback") return null;
  return (
    <Badge
      tone="red"
      className={className}
      title="Seeded demo data — not a verified real property or owner. Do not contact."
    >
      DEMO
    </Badge>
  );
}
