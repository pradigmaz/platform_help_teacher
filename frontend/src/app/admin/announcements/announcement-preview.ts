function stripInlineMarkdown(text: string): string {
  return text
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/~~([^~]+)~~/g, '$1')
    .replace(/`([^`]+)`/g, '$1');
}

export function getAnnouncementPreview(content: string): string {
  const segments = content
    .replace(/\r/g, '')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => {
      if (/^---+$/.test(line) || /^\*\*\*+$/.test(line)) {
        return '';
      }

      const withoutHeading = line.replace(/^#{1,6}\s+/, '');
      const withoutQuote = withoutHeading.replace(/^>\s?/, '');
      const bulletMatch = withoutQuote.match(/^([-*+]|\d+\.)\s+(.*)$/);
      const normalized = stripInlineMarkdown(bulletMatch ? bulletMatch[2] : withoutQuote)
        .replace(/\s+/g, ' ')
        .trim();

      if (!normalized) {
        return '';
      }

      return bulletMatch ? `• ${normalized}` : normalized;
    })
    .filter((line) => line.length > 0);

  return segments.join(' ').replace(/\s+/g, ' ').trim();
}
