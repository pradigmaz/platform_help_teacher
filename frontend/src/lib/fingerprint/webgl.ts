/**
 * WebGL fingerprinting.
 */
import type { WebGLInfo } from './types';

export function getWebGLInfo(): WebGLInfo | undefined {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) return undefined;

    const glCtx = gl as WebGLRenderingContext;
    const debugInfo = glCtx.getExtension('WEBGL_debug_renderer_info');
    
    return {
      vendor: debugInfo 
        ? glCtx.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || 'unknown' 
        : glCtx.getParameter(glCtx.VENDOR),
      renderer: debugInfo 
        ? glCtx.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || 'unknown' 
        : glCtx.getParameter(glCtx.RENDERER),
      version: glCtx.getParameter(glCtx.VERSION),
      shadingLanguageVersion: glCtx.getParameter(glCtx.SHADING_LANGUAGE_VERSION),
      maxTextureSize: glCtx.getParameter(glCtx.MAX_TEXTURE_SIZE),
      maxViewportDims: glCtx.getParameter(glCtx.MAX_VIEWPORT_DIMS),
      maxRenderbufferSize: glCtx.getParameter(glCtx.MAX_RENDERBUFFER_SIZE),
      maxVertexAttribs: glCtx.getParameter(glCtx.MAX_VERTEX_ATTRIBS),
      maxVertexUniformVectors: glCtx.getParameter(glCtx.MAX_VERTEX_UNIFORM_VECTORS),
      maxFragmentUniformVectors: glCtx.getParameter(glCtx.MAX_FRAGMENT_UNIFORM_VECTORS),
      maxVaryingVectors: glCtx.getParameter(glCtx.MAX_VARYING_VECTORS),
      aliasedLineWidthRange: glCtx.getParameter(glCtx.ALIASED_LINE_WIDTH_RANGE),
      aliasedPointSizeRange: glCtx.getParameter(glCtx.ALIASED_POINT_SIZE_RANGE),
      extensions: glCtx.getSupportedExtensions() || [],
    };
  } catch {
    return undefined;
  }
}

export function isWebGL2Available(): boolean {
  return !!document.createElement('canvas').getContext('webgl2');
}
