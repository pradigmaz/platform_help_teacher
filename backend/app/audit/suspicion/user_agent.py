"""User-Agent parsing utilities."""
from typing import Optional, Tuple


def parse_user_agent(ua: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Извлечь browser и OS из User-Agent."""
    if not ua:
        return None, None
    
    ua_lower = ua.lower()
    
    # Browser detection
    browser = None
    if "edg/" in ua_lower:
        browser = "edge"
    elif "chrome/" in ua_lower and "safari/" in ua_lower:
        browser = "chrome"
    elif "firefox/" in ua_lower:
        browser = "firefox"
    elif "safari/" in ua_lower and "chrome/" not in ua_lower:
        browser = "safari"
    elif "opera" in ua_lower or "opr/" in ua_lower:
        browser = "opera"
    
    # OS detection
    os_name = None
    if "windows" in ua_lower:
        os_name = "windows"
    elif "mac os" in ua_lower or "macos" in ua_lower:
        os_name = "macos"
    elif "android" in ua_lower:
        os_name = "android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "ios"
    elif "linux" in ua_lower:
        os_name = "linux"
    
    return browser, os_name
