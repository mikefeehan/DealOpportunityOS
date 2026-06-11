import { PropertyDetailPage } from "@/components/property-detail-page";

export default async function PropertyDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PropertyDetailPage id={id} />;
}
