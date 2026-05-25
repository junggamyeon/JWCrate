from typing import Optional

try:
    from jwplaceholderapi import PlaceholderAPI
    HAS_JWPLACEHOLDERAPI = True
except ImportError:
    HAS_JWPLACEHOLDERAPI = False

def replace_placeholders(text: str, player=None) -> str:
    if not HAS_JWPLACEHOLDERAPI:
        # Fallback basic replacements
        if player:
            text = text.replace("%player%", player.name)
        return text
    
    return PlaceholderAPI.set_placeholders(player, text)
