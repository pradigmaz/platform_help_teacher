'use client';

import * as React from 'react';
import { SubjectsAPI, type GroupSubjectOffering } from '@/lib/api';

export const ADMIN_OFFERINGS_CHANGED_EVENT = 'admin-offerings-changed';

let cachedOfferings: GroupSubjectOffering[] | null = null;
let inFlightOfferingsRequest: Promise<GroupSubjectOffering[]> | null = null;

async function loadAdminOfferings(force = false): Promise<GroupSubjectOffering[]> {
  if (!force && cachedOfferings) {
    return cachedOfferings;
  }

  if (!inFlightOfferingsRequest || force) {
    inFlightOfferingsRequest = SubjectsAPI.listOfferings()
      .then((data) => {
        cachedOfferings = data;
        return data;
      })
      .finally(() => {
        inFlightOfferingsRequest = null;
      });
  }

  return inFlightOfferingsRequest;
}

export function notifyAdminOfferingsChanged() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(ADMIN_OFFERINGS_CHANGED_EVENT));
  }
}

export function useAdminExamOfferings() {
  const [offerings, setOfferings] = React.useState<GroupSubjectOffering[]>(cachedOfferings ?? []);
  const [isLoading, setIsLoading] = React.useState(!cachedOfferings);
  const [error, setError] = React.useState(false);

  const refetch = React.useCallback(async (options?: { force?: boolean }) => {
    const shouldForce = Boolean(options?.force);
    if (shouldForce || !cachedOfferings) {
      setIsLoading(true);
    }

    try {
      const nextOfferings = await loadAdminOfferings(shouldForce);
      setOfferings(nextOfferings);
      setError(false);
      return nextOfferings;
    } catch {
      setError(true);
      if (!cachedOfferings) {
        setOfferings([]);
      }
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!cachedOfferings) {
      void refetch();
    }
  }, [refetch]);

  React.useEffect(() => {
    const handleOfferingsChanged = () => {
      void refetch({ force: true });
    };

    window.addEventListener(ADMIN_OFFERINGS_CHANGED_EVENT, handleOfferingsChanged);
    return () => {
      window.removeEventListener(ADMIN_OFFERINGS_CHANGED_EVENT, handleOfferingsChanged);
    };
  }, [refetch]);

  const examOfferings = React.useMemo(
    () => offerings.filter((offering) => offering.final_control_type === 'exam'),
    [offerings],
  );

  return {
    offerings,
    examOfferings,
    hasExams: examOfferings.length > 0,
    isLoading,
    error,
    refetch,
  };
}
