import { OwnerDetailPage } from "@/components/owner-detail-page";

export default async function OwnerDetail({ params }: { params: Promise<{ ownerName: string }> }) {
  const { ownerName } = await params;
  return <OwnerDetailPage ownerName={decodeURIComponent(ownerName)} />;
}
