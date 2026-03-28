interface FingerprintData {
  canvas?: string;
  webgl?: { vendor: string; renderer: string; extensions?: string[] };
  screen?: { width: number; height: number; colorDepth: number; pixelRatio: number; orientation?: string };
  timezone?: string;
  language?: string;
  platform?: string;
  hardwareConcurrency?: number;
  deviceMemory?: number;
  touchSupport?: boolean;
  maxTouchPoints?: number;
  cookieEnabled?: boolean;
  doNotTrack?: string | null;
  plugins?: string[];
  audio?: string;
  connection?: { type?: string; downlink?: number; rtt?: number; saveData?: boolean };
  mediaDevices?: { cameras: number; microphones: number; speakers: number };
  pdfViewer?: boolean;
  webdriver?: boolean;
  oscpu?: string;
}

type FingerprintKind = "absent" | "missing" | "opaque_hash" | "legacy_structured" | "normalized_replacement";

interface FingerprintEntry {
  label: string;
  value: string;
}

interface FingerprintViewModel {
  kind: FingerprintKind;
  note?: string;
  opaqueHash?: string;
  structured?: FingerprintData;
  summaryEntries: FingerprintEntry[];
  matchingEntries: FingerprintEntry[];
  qualityEntries: FingerprintEntry[];
}

const ENVELOPE_SCHEMA = "fingerprint-migration-v1";

const FIELD_LABELS: Record<string, string> = {
  oscpu: "OS CPU",
  user_agent_family: "User-Agent",
  ip_prefix: "IP prefix",
  match_score: "Match score",
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatLabel(key: string): string {
  if (FIELD_LABELS[key]) return FIELD_LABELS[key];
  const normalized = key.replace(/_/g, " ").trim();
  return normalized ? normalized.charAt(0).toUpperCase() + normalized.slice(1) : key;
}

function formatValue(value: unknown): string {
  if (typeof value === "boolean") return value ? "Да" : "Нет";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "—";
  if (typeof value === "string") return value || "—";
  if (Array.isArray(value)) return value.map(formatValue).join(", ");
  if (isRecord(value)) return JSON.stringify(value);
  return "—";
}

function toEntries(value: unknown): FingerprintEntry[] {
  if (!isRecord(value)) return [];
  return Object.entries(value).flatMap(([key, entryValue]) => {
    if (entryValue === undefined || entryValue === null || entryValue === "") return [];
    return [{ label: formatLabel(key), value: formatValue(entryValue) }];
  });
}

function getEnvelopeKind(record: Record<string, unknown>): FingerprintKind | null {
  const explicitKind = record.kind;
  if (
    explicitKind === "missing" ||
    explicitKind === "opaque_hash" ||
    explicitKind === "legacy_structured" ||
    explicitKind === "normalized_replacement"
  ) {
    return explicitKind;
  }
  if (typeof record.opaque_hash === "string") return "opaque_hash";
  if (isRecord(record.normalized_summary) || isRecord(record.normalized_matching)) return "normalized_replacement";
  if (isRecord(record.raw_payload)) return "legacy_structured";
  return null;
}

export type { FingerprintData, FingerprintEntry, FingerprintKind, FingerprintViewModel };

export function getFingerprintViewModel(fingerprint: unknown): FingerprintViewModel {
  if (!isRecord(fingerprint) || Object.keys(fingerprint).length === 0) {
    return {
      kind: "absent",
      summaryEntries: [],
      matchingEntries: [],
      qualityEntries: [],
    };
  }

  const qualityEntries = toEntries(fingerprint.quality);
  const isEnvelope = fingerprint.schema === ENVELOPE_SCHEMA || "kind" in fingerprint;

  if (isEnvelope) {
    const kind = getEnvelopeKind(fingerprint);

    if (!kind) {
      console.warn("[AuditFingerprintSection] Unsupported fingerprint envelope", fingerprint);
      return {
        kind: "missing",
        note: "Fingerprint сохранён в неподдерживаемом формате.",
        summaryEntries: [],
        matchingEntries: [],
        qualityEntries,
      };
    }

    if (kind === "missing") {
      return {
        kind,
        note: "Fingerprint для этой записи не сохранён.",
        summaryEntries: [],
        matchingEntries: [],
        qualityEntries,
      };
    }

    if (kind === "opaque_hash") {
      return {
        kind,
        note: "Доступен только непрозрачный хеш fingerprint без исходного payload.",
        opaqueHash: typeof fingerprint.opaque_hash === "string" ? fingerprint.opaque_hash : undefined,
        summaryEntries: [],
        matchingEntries: [],
        qualityEntries,
      };
    }

    if (kind === "normalized_replacement") {
      return {
        kind,
        note: "Показана нормализованная сводка fingerprint без полного сырого payload.",
        opaqueHash: typeof fingerprint.opaque_hash === "string" ? fingerprint.opaque_hash : undefined,
        summaryEntries: toEntries(fingerprint.normalized_summary),
        matchingEntries: toEntries(fingerprint.normalized_matching),
        qualityEntries,
      };
    }

    if (isRecord(fingerprint.raw_payload)) {
      return {
        kind,
        note: "Показан legacy fingerprint, вложенный в envelope нового формата.",
        structured: fingerprint.raw_payload as FingerprintData,
        summaryEntries: [],
        matchingEntries: [],
        qualityEntries,
      };
    }

    return {
      kind: "missing",
      note: "В записи заявлен structured fingerprint, но payload отсутствует.",
      summaryEntries: [],
      matchingEntries: [],
      qualityEntries,
    };
  }

  if (isRecord(fingerprint.normalized_summary) || isRecord(fingerprint.normalized_matching)) {
    return {
      kind: "normalized_replacement",
      note: "Показана нормализованная сводка fingerprint.",
      opaqueHash: typeof fingerprint.opaque_hash === "string" ? fingerprint.opaque_hash : undefined,
      summaryEntries: toEntries(fingerprint.normalized_summary),
      matchingEntries: toEntries(fingerprint.normalized_matching),
      qualityEntries,
    };
  }

  if (typeof fingerprint.opaque_hash === "string") {
    return {
      kind: "opaque_hash",
      note: "Доступен только непрозрачный хеш fingerprint.",
      opaqueHash: fingerprint.opaque_hash,
      summaryEntries: [],
      matchingEntries: [],
      qualityEntries,
    };
  }

  return {
    kind: "legacy_structured",
    structured: fingerprint as FingerprintData,
    summaryEntries: [],
    matchingEntries: [],
    qualityEntries,
  };
}
