import { PublicReportClient } from './PublicReportClient';
import { parseReportAttestation } from './reportNavigation';

interface PageProps {
  params: Promise<{ code: string }>;
  searchParams: Promise<{ attestation?: string }>;
}

export default async function PublicReportPage({ params, searchParams }: PageProps) {
  const { code } = await params;
  const { attestation } = await searchParams;

  return (
    <PublicReportClient
      code={code}
      initialAttestationType={parseReportAttestation(attestation)}
    />
  );
}
