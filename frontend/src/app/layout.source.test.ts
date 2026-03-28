import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

describe('RootLayout legacy fingerprint cleanup', () => {
  it('does not mount the legacy fingerprint initializer', () => {
    const source = readFileSync(path.resolve(process.cwd(), 'src/app/layout.tsx'), 'utf8');

    expect(source).not.toContain('FingerprintInitializer');
    expect(source).not.toContain('isFingerprintCollectionEnabled()');
    expect(source).not.toContain('X-Device-Fingerprint');
  });
});
