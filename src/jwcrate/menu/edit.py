from endstone import Player, ColorFormat
from endstone.inventory import ItemStack
from endstone.plugin import Plugin

from jwcrate.api.models import Crate
from jwcrate.crate.manager import CrateManager
from jwcrate.messages import msg
from jwcrate.utils.config_loader import load_yaml, save_yaml


class EditMenu:
    def __init__(self, plugin: Plugin, crate: Crate, crate_manager: CrateManager):
        self.plugin = plugin
        self.crate = crate
        self.crate_manager = crate_manager
        self.menu = None

    def open(self, player: Player):
        from jwinventoryapi import Menu, MenuType

        self.menu = Menu(MenuType.DOUBLE_CHEST, f"Edit: {self.crate.name}")
        self.menu.set_editable(True)

        rewards = list(self.crate.rewards.values())
        for i, reward in enumerate(rewards):
            if i >= 54:
                break
            self.menu.set_item(i, self._reward_item(reward))

        self.menu.set_close_listener(self._on_close)
        self.menu.send_to(player)

    def _on_close(self, player: Player):
        def do_save():
            try:
                inv = self.menu.inventory
                items_data = []

                for i in range(54):
                    item = inv.get_item(i)
                    if item is None or "air" in item.type.id.lower():
                        continue
                    items_data.append(self._serialize_item(item, i))

                if not items_data:
                    player.send_message(msg("edit_empty"))
                    return

                self._save_rewards(items_data)
                self.crate_manager.load_all()
                player.send_message(msg("edit_saved", count=len(items_data), crate=self.crate.name))
            except Exception as e:
                player.send_message(msg("edit_error", error=str(e)))
                self.plugin.logger.error(f"Error saving edit rewards: {e}")

        self.plugin.server.scheduler.run_task(self.plugin, do_save, delay=1)

    def _reward_item(self, reward) -> ItemStack:
        item = ItemStack(reward.preview.get("type", "minecraft:paper"), reward.preview.get("amount", 1))
        meta = item.item_meta
        if reward.preview.get("name"):
            meta.display_name = reward.preview["name"]
        if "lore" in reward.preview:
            meta.lore = reward.preview["lore"]
        if "enchantments" in reward.preview:
            for ench_name, level in reward.preview["enchantments"].items():
                meta.add_enchant(ench_name, level, True)
        item.set_item_meta(meta)
        return item

    def _serialize_item(self, item: ItemStack, index: int) -> dict:
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

    def _save_rewards(self, items_data: list):
        crates_dir = self.crate_manager.data_folder / "crates"
        file = crates_dir / f"{self.crate.id}.yml"
        config = load_yaml(file)

        if "Rewards" not in config:
            config["Rewards"] = {}
        if "List" not in config["Rewards"]:
            config["Rewards"]["List"] = {}

        new_rewards = {}
        for entry in items_data:
            item = entry["item"]
            idx = entry["index"]
            reward_id = f"reward_{idx}"

            # Resolve name: use display name if present, otherwise derive from type
            if "name" in item:
                reward_name = item["name"]
            else:
                reward_name = item["type"].replace("minecraft:", "").replace("_", " ").title()

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
                "Name": reward_name,
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
