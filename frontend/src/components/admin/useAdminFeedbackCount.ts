"use client";

import { useAdminSession } from "./AdminSessionProvider";

export function useAdminFeedbackCount() {
  return useAdminSession().feedbackCount;
}
