export type ToolbarPreset = 'full' | 'practice' | 'minimal' | 'none';

export interface PresetConfig {
  showHistory: boolean;
  showTextFormat: boolean;
  showHeadings: boolean;
  showLists: boolean;
  showAlign: boolean;
  showIndent: boolean;
  showFontSize: boolean;
  showInsert: boolean;
  showSave: boolean;
  minHeight: string;
  padding: string;
}

export const PRESETS: Record<ToolbarPreset, PresetConfig> = {
  // Полный тулбар для лекций
  full: {
    showHistory: true,
    showTextFormat: true,
    showHeadings: true,
    showLists: true,
    showAlign: true,
    showIndent: true,
    showFontSize: true,
    showInsert: true,
    showSave: true,
    minHeight: '400px',
    padding: 'px-4 py-4',
  },
  // Для практики — без шрифтов и выравнивания (наследует от теории)
  practice: {
    showHistory: true,
    showTextFormat: true,
    showHeadings: true,
    showLists: true,
    showAlign: false,
    showIndent: false,
    showFontSize: false,
    showInsert: true,
    showSave: false,
    minHeight: '300px',
    padding: 'px-4 py-3',
  },
  // Минимальный для вариантов — текст + списки + история + таблицы
  minimal: {
    showHistory: true,
    showTextFormat: true,
    showHeadings: false,
    showLists: true,
    showAlign: false,
    showIndent: false,
    showFontSize: false,
    showInsert: true,
    showSave: false,
    minHeight: '120px',
    padding: 'px-3 py-2',
  },
  // Без тулбара
  none: {
    showHistory: false,
    showTextFormat: false,
    showHeadings: false,
    showLists: false,
    showAlign: false,
    showIndent: false,
    showFontSize: false,
    showInsert: false,
    showSave: false,
    minHeight: '100px',
    padding: 'px-3 py-2',
  },
};

export function getPresetConfig(preset: ToolbarPreset): PresetConfig {
  return PRESETS[preset];
}
