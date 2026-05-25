from endstone import Player, ColorFormat
from endstone.inventory import ItemStack
from endstone.plugin import Plugin
from typing import Any

from jwcrate.api.models import Crate
from jwcrate.crate.manager import CrateManager
from jwcrate.utils.config_loader import load_yaml, save_yaml


class EditMenu:
    """Opens a chest for admin to place reward items. Saves full NBT on close."""

    def __init__(self, plugin: Plugin, crate: Crate, crate_manager: CrateManager):
        self.plugin = plugin
        self.crate = crate
        self.crate_manager = crate_manager
        self.menu = None

    def open(self, player: Player):
        from jwinventoryapi import Menu, MenuType

        self.menu = Menu(MenuType.DOUBLE_CHEST, f"Edit: {self.crate.name}")
        self.menu.set_editable(True)

        # Pre-fill with existing rewards
        rewards = list(self.crate.rewards.values())
        for i, reward in enumerate(rewards):
            if i >= 54:
                break
            item = self._reward_to_itemstack(reward)
            self.menu.set_item(i, item)

        self.menu.set_close_listener(self._on_close_handler)
        self.menu.send_to(player)

    def _on_close_handler(self, player: Player):
        """Save all items in the menu as rewards to the crate config."""
        def do_save():
            try:
                inv = self.menu.inventory
                items_data = []

                for i in range(54):
                    item = inv.get_item(i)
                    if item is None:
                        continue
                    if "air" in item.type.id.lower():
                        continue
                    items_data.append(self._serialize_item(item, i))

                if not items_data:
                    player.send_message(f"{ColorFormat.YELLOW}No items found. Rewards not changed.")
                    return

                # Save to config
                self._save_rewards_to_config(items_data)
                # Reload crate
                self.crate_manager.load_all()
                player.send_message(
                    f"{ColorFormat.GREEN}Saved {len(items_data)} reward(s) for '{self.crate.name}'! "
                    f"Edit the config to adjust weights/rarity, then /jwcrate reload."
                )
            except Exception as e:
                player.send_message(f"{ColorFormat.RED}Error saving rewards: {e}")
                self.plugin.logger.error(f"Error saving edit rewards: {e}")

        self.plugin.server.scheduler.run_task(self.plugin, do_save, delay=1)

    def _reward_to_itemstack(self, reward) -> ItemStack:
        """Convert a reward to an ItemStack for display."""
        item_type = reward.preview.get("type", "minecraft:paper")
        amount = reward.preview.get("amount", 1)
        item = ItemStack(item_type, amount)
        meta = item.item_meta
        if reward.preview.get("name"):
            meta.display_name = reward.preview.get("name")
        if "lore" in reward.preview:
            meta.lore = reward.preview["lore"]
        if "enchantments" in reward.preview:
            for ench_name, level in reward.preview["enchantments"].items():
                meta.add_enchant(ench_name, level, True)
        item.set_item_meta(meta)
        return item

    def _serialize_item(self, item: ItemStack, index: int) -> dict:
        """Serialize an ItemStack to a dict with full NBT data."""
        meta = item.item_meta
        data = {
            "type": item.type.id,
            "amount": item.amount,
        }

        if hasattr(item, 'data') and item.data != 0:
            data["data"] = item.data

        if meta:
            if meta.has_display_name:
                data["name"] = meta.display_name
            if meta.has_lore:
                data["lore"] = list(meta.lore)
            if meta.has_enchants:
                enchants = {}
                for ench_name, level in meta.enchants.items():
                    enchants[str(ench_name)] = level
                data["enchantments"] = enchants
            if meta.is_unbreakable:
                data["unbreakable"] = True

        return {"index": index, "item": data}

    def _save_rewards_to_config(self, items_data: list):
        """Write rewards to the crate YAML config file."""
        crates_dir = self.crate_manager.data_folder / "crates"
        file = crates_dir / f"{self.crate.id}.yml"
        config = load_yaml(file)

        if "Rewards" not in config:
            config["Rewards"] = {}
        if "List" not in config["Rewards"]:
            config["Rewards"]["List"] = {}

        # Clear existing rewards and rebuild from items
        new_rewards = {}
        for entry in items_data:
            item = entry["item"]
            idx = entry["index"]
            reward_id = f"reward_{idx}"

            # Build preview data (same as item data for display)
            preview = {
                "type": item["type"],
                "amount": item.get("amount", 1),
            }
            if "name" in item:
                preview["name"] = item["name"]
            if "lore" in item:
                preview["lore"] = item["lore"]
            if "enchantments" in item:
                preview["enchantments"] = item["enchantments"]

            # Build items data for giving
            give_item = {
                "type": item["type"],
                "amount": item.get("amount", 1),
            }
            if "name" in item:
                give_item["name"] = item["name"]
            if "lore" in item:
                give_item["lore"] = item["lore"]
            if "enchantments" in item:
                give_item["enchantments"] = item["enchantments"]
            if "unbreakable" in item:
                give_item["unbreakable"] = item["unbreakable"]
            if "data" in item:
                give_item["data"] = item["data"]

            new_rewards[reward_id] = {
                "Type": "ITEM",
                "Weight": 10.0,
                "Rarity": "common",
                "PreviewData": preview,
                "ItemsData": [give_item],
                "Commands": [],
                "Broadcast": False
            }

        config["Rewards"]["List"] = new_rewards
        save_yaml(file, config)
