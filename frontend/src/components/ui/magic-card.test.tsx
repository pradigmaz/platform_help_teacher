import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { MagicCard } from './magic-card';

describe('MagicCard', () => {
  it('does not apply the fallback pink gradient without explicit gradient stops', () => {
    const { container } = render(<MagicCard>content</MagicCard>);

    const overlay = container.querySelector('[style*="radial-gradient"]');
    expect(overlay).toBeTruthy();
    expect(overlay?.getAttribute('style')).not.toContain('linear-gradient(135deg');
    expect(overlay?.getAttribute('style')).not.toContain('#9E7AFF');
    expect(overlay?.getAttribute('style')).not.toContain('#FE8BBB');
  });

  it('keeps the linear gradient when explicit gradient stops are provided', () => {
    const { container } = render(
      <MagicCard gradientFrom="#22c55e" gradientTo="#10b981">
        content
      </MagicCard>
    );

    const overlay = container.querySelector('[style*="radial-gradient"]');
    expect(overlay).toBeTruthy();
    expect(overlay?.getAttribute('style')).toContain('linear-gradient(135deg');
    expect(overlay?.getAttribute('style')).toContain('rgb(34, 197, 94)');
    expect(overlay?.getAttribute('style')).toContain('rgb(16, 185, 129)');
  });
});
