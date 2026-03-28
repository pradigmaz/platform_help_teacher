import { describe, expect, it } from "vitest";

import { getFingerprintViewModel } from "./auditFingerprintModel";

describe("getFingerprintViewModel", () => {
  it("keeps historical raw fingerprint payloads as structured", () => {
    const model = getFingerprintViewModel({
      platform: "Win32",
      language: "ru-RU",
      screen: { width: 1920, height: 1080, colorDepth: 24, pixelRatio: 1 },
    });

    expect(model.kind).toBe("legacy_structured");
    expect(model.structured?.platform).toBe("Win32");
  });

  it("supports missing envelope payloads", () => {
    const model = getFingerprintViewModel({
      schema: "fingerprint-migration-v1",
      kind: "missing",
      quality: { completeness: "missing" },
    });

    expect(model.kind).toBe("missing");
    expect(model.note).toContain("не сохранён");
    expect(model.qualityEntries).toEqual([{ label: "Completeness", value: "missing" }]);
  });

  it("supports opaque hash envelopes", () => {
    const model = getFingerprintViewModel({
      schema: "fingerprint-migration-v1",
      kind: "opaque_hash",
      opaque_hash: "sha256:abc123",
    });

    expect(model.kind).toBe("opaque_hash");
    expect(model.opaqueHash).toBe("sha256:abc123");
    expect(model.structured).toBeUndefined();
  });

  it("supports normalized replacement envelopes", () => {
    const model = getFingerprintViewModel({
      schema: "fingerprint-migration-v1",
      kind: "normalized_replacement",
      normalized_summary: {
        browser_family: "Chrome",
        platform_family: "Windows",
      },
      normalized_matching: {
        matched_components: ["browser_family", "platform_family"],
      },
      quality: {
        completeness: "reduced",
      },
    });

    expect(model.kind).toBe("normalized_replacement");
    expect(model.summaryEntries).toEqual([
      { label: "Browser family", value: "Chrome" },
      { label: "Platform family", value: "Windows" },
    ]);
    expect(model.matchingEntries).toEqual([
      { label: "Matched components", value: "browser_family, platform_family" },
    ]);
    expect(model.qualityEntries).toEqual([{ label: "Completeness", value: "reduced" }]);
  });

  it("unwraps legacy structured payloads from the new envelope", () => {
    const model = getFingerprintViewModel({
      schema: "fingerprint-migration-v1",
      kind: "legacy_structured",
      raw_payload: {
        platform: "Linux x86_64",
        hardwareConcurrency: 8,
      },
    });

    expect(model.kind).toBe("legacy_structured");
    expect(model.structured?.platform).toBe("Linux x86_64");
    expect(model.structured?.hardwareConcurrency).toBe(8);
  });
});
