import { PublicReportClient } from './PublicReportClient';

interface PageProps {
  params: Promise<{ code: string }>;
}

export default async function PublicReportPage({ params }: PageProps) {
  const { code } = await params;
  return <PublicReportClient code={code} />;
}
