/**
 * Canvas fingerprinting.
 */

export function getCanvasFingerprint(): string | undefined {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return undefined;

    canvas.width = 280;
    canvas.height = 60;

    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = '#f60';
    ctx.fillRect(100, 1, 80, 50);
    
    ctx.fillStyle = '#069';
    ctx.font = '11pt Arial';
    ctx.fillText('Cwm fjordbank', 2, 15);
    
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.font = '18pt Arial';
    ctx.fillText('glyphs vext', 4, 45);
    
    // Emoji для различия ОС
    ctx.font = '14pt Arial';
    ctx.fillText('😀🔥💻', 180, 30);
    
    ctx.beginPath();
    ctx.arc(50, 50, 20, 0, Math.PI * 2);
    ctx.stroke();

    return canvas.toDataURL().slice(-100);
  } catch {
    return undefined;
  }
}

export function getCanvasGeometry(): string | undefined {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return undefined;

    canvas.width = 100;
    canvas.height = 100;

    ctx.beginPath();
    ctx.moveTo(20, 20);
    ctx.bezierCurveTo(20, 100, 200, 100, 200, 20);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.arc(50, 50, 30, 0, Math.PI * 2);
    ctx.fill();

    return canvas.toDataURL().slice(-50);
  } catch {
    return undefined;
  }
}
