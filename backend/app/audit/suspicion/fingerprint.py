"""Fingerprint extraction и matching utilities."""
from typing import Optional, Dict, Any, List, Tuple

from .constants import (
    SCORE_WEBGL, SCORE_SCREEN, SCORE_PLATFORM, SCORE_CANVAS,
    SCORE_UA_BROWSER, SCORE_UA_OS,
)
from .user_agent import parse_user_agent


def extract_webgl_key(fp: Dict[str, Any]) -> Optional[str]:
    """Извлечь ключ WebGL."""
    webgl = fp.get("webgl")
    if webgl and isinstance(webgl, dict):
        vendor = webgl.get("vendor", "")
        renderer = webgl.get("renderer", "")
        if vendor and renderer:
            return f"{vendor}|{renderer}"
    return None


def extract_screen_key(fp: Dict[str, Any]) -> Optional[str]:
    """Извлечь ключ screen."""
    screen = fp.get("screen")
    if screen and isinstance(screen, dict):
        w = screen.get("width")
        h = screen.get("height")
        depth = screen.get("colorDepth")
        if w and h:
            return f"{w}x{h}x{depth or 24}"
    return None


def extract_platform_key(fp: Dict[str, Any]) -> Optional[str]:
    """Извлечь ключ platform."""
    platform = fp.get("platform", "")
    cores = fp.get("hardwareConcurrency", 0)
    if platform:
        return f"{platform}|{cores}"
    return None


def detect_inconsistencies(fp: Dict[str, Any]) -> List[str]:
    """
    Детектит нереалистичные комбинации (признак антидетект браузера).
    """
    issues = []
    
    webgl = fp.get("webgl", {})
    renderer = webgl.get("renderer", "").lower() if webgl else ""
    cores = fp.get("hardwareConcurrency", 0)
    platform = fp.get("platform", "").lower()
    
    # Мощный GPU но мало ядер — подозрительно
    powerful_gpu_keywords = ["rtx", "gtx", "radeon rx", "nvidia", "geforce"]
    has_powerful_gpu = any(kw in renderer for kw in powerful_gpu_keywords)
    if has_powerful_gpu and cores and cores < 4:
        issues.append("powerful_gpu_low_cores")
    
    # Mac platform но Windows в renderer
    if "mac" in platform and "windows" in renderer:
        issues.append("platform_renderer_mismatch")
    
    # Linux platform но DirectX в renderer
    if "linux" in platform and ("d3d" in renderer or "direct" in renderer):
        issues.append("linux_directx_mismatch")
    
    # Очень старый GPU с новым браузером — может быть спуфинг
    old_gpu_keywords = ["intel hd 3000", "intel hd 4000", "geforce 8", "geforce 9"]
    has_old_gpu = any(kw in renderer for kw in old_gpu_keywords)
    if has_old_gpu and cores and cores >= 8:
        issues.append("old_gpu_many_cores")
    
    return issues


def calculate_fingerprint_score(
    fp1: Dict[str, Any],
    fp2: Dict[str, Any],
    ua1: Optional[str] = None,
    ua2: Optional[str] = None,
) -> Tuple[int, List[str]]:
    """Рассчитать score совпадения двух fingerprints."""
    score = 0
    matches = []
    
    # WebGL
    webgl1 = extract_webgl_key(fp1)
    webgl2 = extract_webgl_key(fp2)
    if webgl1 and webgl2 and webgl1 == webgl2:
        score += SCORE_WEBGL
        matches.append("webgl")
    
    # Screen
    screen1 = extract_screen_key(fp1)
    screen2 = extract_screen_key(fp2)
    if screen1 and screen2 and screen1 == screen2:
        score += SCORE_SCREEN
        matches.append("screen")
    
    # Platform
    platform1 = extract_platform_key(fp1)
    platform2 = extract_platform_key(fp2)
    if platform1 and platform2 and platform1 == platform2:
        score += SCORE_PLATFORM
        matches.append("platform")
    
    # Canvas
    canvas1 = fp1.get("canvas")
    canvas2 = fp2.get("canvas")
    if canvas1 and canvas2 and canvas1 == canvas2:
        score += SCORE_CANVAS
        matches.append("canvas")
    
    # User-Agent
    if ua1 and ua2:
        browser1, os1 = parse_user_agent(ua1)
        browser2, os2 = parse_user_agent(ua2)
        if browser1 and browser2 and browser1 == browser2:
            score += SCORE_UA_BROWSER
            matches.append("browser")
        if os1 and os2 and os1 == os2:
            score += SCORE_UA_OS
            matches.append("os")
    
    return score, matches
