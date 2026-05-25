from pathlib import Path
from typing import Dict

from jwcrate.utils.config_loader import load_yaml, save_yaml

_DEFAULT_MESSAGES = {
    "no_permission": "&cNo permission.",
    "player_only": "&cPlayer only command.",
    "reload_success": "&aReloaded crates and keys.",
    "crate_not_found": "&cCrate '{crate}' not found.",
    "key_not_found": "&cKey '{key}' not found.",
    "player_not_found": "&cPlayer not found.",
    "give_crate_success": "&aGave {amount} {crate} to {player}.",
    "give_key_success": "&aGave {amount} {key} to {player}.",
    "give_virtual_key_success": "&aGave {amount} virtual {key} to {player}.",
    "set_instruction": "&aRight-click a block to set the crate location for '{crate}'.",
    "set_success": "&aCrate location for '{crate}' set successfully!",
    "set_crate_gone": "&cCrate '{crate}' no longer exists.",
    "block_removed": "&eCrate block removed.",
    "block_break_denied": "&cYou cannot break a crate block.",
    "no_permission_crate": "&cYou don't have permission to open this crate.",
    "cooldown": "&cCrate is on cooldown for {seconds}s.",
    "cannot_afford": "&cYou cannot afford to open this crate.",
    "reward_win": "&aYou won &f{reward}&a!",
    "reward_broadcast": "&6{player} won &f{reward}&6 from {crate}!",
    "edit_saved": "&aSaved {count} reward(s) for '{crate}'! Edit the config to adjust weights/rarity, then /jwcrate reload.",
    "edit_empty": "&eNo items found. Rewards not changed.",
    "edit_error": "&cError saving rewards: {error}",
    "usage_give": "&cUsage: /jwcrate give <player> <crate_id> [amount]",
    "usage_key_give": "&cUsage: /jwcrate key give <player> <key_id> [amount]",
    "usage_open": "&cUsage: /jwcrate open <crate_id>",
    "usage_set": "&cUsage: /jwcrate set <crate_id>",
    "usage_preview": "&cUsage: /jwcrate preview <crate_id>",
    "usage_edit": "&cUsage: /jwcrate edit <crate_id>",
    "help_header": "&e--- JWCrate Help ---",
    "help_reload": "/jwcrate reload - Reload config",
    "help_give": "/jwcrate give <player> <crate> [amount] - Give physical crate",
    "help_key_give": "/jwcrate key give <player> <key> [amount] - Give key",
    "help_open": "/jwcrate open <crate> - Open crate virtually",
    "help_preview": "/jwcrate preview <crate> - Preview crate",
    "help_edit": "/jwcrate edit <crate> - Edit crate rewards",
    "help_set": "/jwcrate set <crate> - Set crate block location",
}

_COLOR_MAP = {
    "&0": "\u00a70", "&1": "\u00a71", "&2": "\u00a72", "&3": "\u00a73",
    "&4": "\u00a74", "&5": "\u00a75", "&6": "\u00a76", "&7": "\u00a77",
    "&8": "\u00a78", "&9": "\u00a79", "&a": "\u00a7a", "&b": "\u00a7b",
    "&c": "\u00a7c", "&d": "\u00a7d", "&e": "\u00a7e", "&f": "\u00a7f",
    "&l": "\u00a7l", "&o": "\u00a7o", "&n": "\u00a7n", "&m": "\u00a7m",
    "&k": "\u00a7k", "&r": "\u00a7r",
}

_messages: Dict[str, str] = {}


def load_messages(data_folder: Path):
    global _messages
    file = data_folder / "messages.yml"
    _messages = load_yaml(file, _DEFAULT_MESSAGES)
    # Save back so new keys are added
    save_yaml(file, _messages)


def msg(msg_id: str, **kwargs) -> str:
    raw = _messages.get(msg_id, _DEFAULT_MESSAGES.get(msg_id, msg_id))
    if kwargs:
        raw = raw.format(**kwargs)
    for code, section in _COLOR_MAP.items():
        raw = raw.replace(code, section)
    return raw
