export type Theme = 'light' | 'dark' | 'sepia';
export type FontFamily = 'sans' | 'serif' | 'mono';

export interface ReaderSettings {
  theme: Theme;
  fontFamily: FontFamily;
  fontSize: number; // 14-24
}

export interface TOCItem {
  id: string;
  text: string;
  level: number;
}
