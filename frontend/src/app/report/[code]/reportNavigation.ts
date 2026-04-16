export type ReportAttestation = 'first' | 'second';

export function parseReportAttestation(value: string | null | undefined): ReportAttestation {
  return value === 'second' ? 'second' : 'first';
}

export function parseReportSubjectId(value: string | null | undefined): string | null {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

export function withReportNavigation(
  searchParams: URLSearchParams,
  attestation: ReportAttestation,
  subjectId?: string | null,
): URLSearchParams {
  const nextParams = new URLSearchParams(searchParams.toString());

  if (attestation === 'second') {
    nextParams.set('attestation', attestation);
  } else {
    nextParams.delete('attestation');
  }

  if (subjectId) {
    nextParams.set('subject_id', subjectId);
  } else {
    nextParams.delete('subject_id');
  }

  return nextParams;
}

export function buildReportHref(code: string, attestation: ReportAttestation, subjectId?: string | null): string {
  const params = withReportNavigation(new URLSearchParams(), attestation, subjectId);
  const query = params.toString();
  return query ? `/report/${code}?${query}` : `/report/${code}`;
}

export function buildStudentReportHref(
  code: string,
  studentId: string,
  attestation: ReportAttestation,
  subjectId?: string | null,
): string {
  const params = withReportNavigation(new URLSearchParams(), attestation, subjectId);
  const query = params.toString();
  const path = `/report/${code}/student/${studentId}`;
  return query ? `${path}?${query}` : path;
}
