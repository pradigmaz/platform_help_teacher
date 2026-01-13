/**
 * Network connection info.
 */
import type { ConnectionInfo } from './types';

export function getConnectionInfo(): ConnectionInfo | undefined {
  try {
    const conn = (navigator as any).connection || 
                 (navigator as any).mozConnection || 
                 (navigator as any).webkitConnection;
    if (!conn) return undefined;
    return {
      type: conn.type,
      effectiveType: conn.effectiveType,
      downlink: conn.downlink,
      downlinkMax: conn.downlinkMax,
      rtt: conn.rtt,
      saveData: conn.saveData,
    };
  } catch {
    return undefined;
  }
}
