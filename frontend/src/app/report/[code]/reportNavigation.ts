export type ReportAttestation = 'first' | 'second';

export function parseReportAttestation(value: string | null | undefined): ReportAttestation {
  return value === 'second' ? 'second' : 'first';
}

export function withReportAttestation(
  searchParams: URLSearchParams,
  attestation: ReportAttestation,
): URLSearchParams {
  const nextParams = new URLSearchParams(searchParams.toString());

  if (attestation === 'second') {
    nextParams.set('attestation', attestation);
  } else {
    nextParams.delete('attestation');
  }

  return nextParams;
}

export function buildReportHref(code: string, attestation: ReportAttestation): string {
  const params = withReportAttestation(new URLSearchParams(), attestation);
  const query = params.toString();
  return query ? `/report/${code}?${query}` : `/report/${code}`;
}

export function buildStudentReportHref(
  code: string,
  studentId: string,
  attestation: ReportAttestation,
): string {
  const params = withReportAttestation(new URLSearchParams(), attestation);
  const query = params.toString();
  const path = `/report/${code}/student/${studentId}`;
  return query ? `${path}?${query}` : path;
}
