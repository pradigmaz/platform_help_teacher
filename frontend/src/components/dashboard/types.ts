/**
 * Types for student dashboard components
 */

import type { StudentLab, StudentAttestation, StudentAttendance } from '@/lib/api';

/** Props for StatusHero component */
export interface StatusHeroProps {
  attestation: StudentAttestation | null;
  isLoading?: boolean;
}

/** Props for QuickStats component */
export interface QuickStatsProps {
  labs: StudentLab[];
  attendance: StudentAttendance | null;
  isLoading?: boolean;
}

/** Props for DeadlinesList component */
export interface DeadlinesListProps {
  labs: StudentLab[];
  maxItems?: number;
}

/** Props for EmptyState component */
export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

/** Lab status for display */
export type LabStatus = 'accepted' | 'pending' | 'rejected' | 'not_submitted';

/** Attestation status */
export type AttestationStatus = 'passing' | 'failing' | 'borderline' | 'unavailable';
