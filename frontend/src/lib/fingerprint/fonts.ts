/**
 * Font detection fingerprinting.
 */

const TEST_FONTS = [
  'Arial', 'Arial Black', 'Arial Narrow', 'Calibri', 'Cambria', 'Cambria Math',
  'Comic Sans MS', 'Consolas', 'Courier', 'Courier New', 'Georgia', 'Helvetica',
  'Impact', 'Lucida Console', 'Lucida Sans Unicode', 'Microsoft Sans Serif',
  'Palatino Linotype', 'Segoe UI', 'Tahoma', 'Times', 'Times New Roman',
  'Trebuchet MS', 'Verdana', 'Wingdings', 'Roboto', 'Open Sans', 'Ubuntu',
  'Droid Sans', 'Liberation Sans', 'DejaVu Sans', 'Noto Sans',
];

const BASE_FONTS = ['monospace', 'sans-serif', 'serif'];

export function detectFonts(): string[] {
  const detected: string[] = [];
  
  try {
    const span = document.createElement('span');
    span.style.position = 'absolute';
    span.style.left = '-9999px';
    span.style.fontSize = '72px';
    span.textContent = 'mmmmmmmmmmlli';
    document.body.appendChild(span);
    
    const baseWidths: Record<string, number> = {};
    for (const base of BASE_FONTS) {
      span.style.fontFamily = base;
      baseWidths[base] = span.offsetWidth;
    }
    
    for (const font of TEST_FONTS) {
      for (const base of BASE_FONTS) {
        span.style.fontFamily = `'${font}', ${base}`;
        if (span.offsetWidth !== baseWidths[base]) {
          detected.push(font);
          break;
        }
      }
    }
    
    document.body.removeChild(span);
  } catch {}
  
  return detected;
}
