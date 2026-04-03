"use client";

import * as React from "react";
import api from "@/lib/api";

export function useAdminFeedbackCount() {
  const [count, setCount] = React.useState(0);

  React.useEffect(() => {
    const fetchCount = async () => {
      try {
        const { data } = await api.get("/feedback/count/new");
        setCount(data.count);
      } catch {
        // Ignore - user might not be admin.
      }
    };

    void fetchCount();
    const interval = setInterval(fetchCount, 60_000);
    return () => clearInterval(interval);
  }, []);

  return count;
}
