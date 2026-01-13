/**
 * Network connection info.
 */
import type { ConnectionInfo } from './types';

interface NetworkInformation {
  type?: string;
  effectiveType?: string;
  downlink?: number;
  downlinkMax?: number;
  rtt?: number;
  saveData?: boolean;
}

interface NavigatorWithConnection extends Navigator {
  connection?: NetworkInformation;
  mozConnection?: NetworkInformation;
  webkitConnection?: NetworkInformation;
}

export function getConnectionInfo(): ConnectionInfo | undefined {
  try {
    const nav = navigator as NavigatorWithConnection;
    const conn = nav.connection || nav.mozConnection || nav.webkitConnection;
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
