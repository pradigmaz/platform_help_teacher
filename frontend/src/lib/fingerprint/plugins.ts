/**
 * Browser plugins and MIME types.
 */

export function getPlugins(): string[] {
  try {
    const plugins: string[] = [];
    for (let i = 0; i < navigator.plugins.length && i < 20; i++) {
      plugins.push(navigator.plugins[i].name);
    }
    return plugins;
  } catch {
    return [];
  }
}

export function getMimeTypes(): string[] {
  try {
    const types: string[] = [];
    for (let i = 0; i < navigator.mimeTypes.length && i < 30; i++) {
      types.push(navigator.mimeTypes[i].type);
    }
    return types;
  } catch {
    return [];
  }
}
