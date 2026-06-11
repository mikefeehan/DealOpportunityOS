import { Badge } from "@/components/ui/badge";

export function RecommendationBadge({ value }: { value: string }) {
  if (value === "Call Owner") return <Badge tone="green">CALL OWNER</Badge>;
  if (value === "Ignore") return <Badge tone="red">IGNORE</Badge>;
  return <Badge tone="amber">MONITOR</Badge>;
}
