from endstone import Player
from endstone.inventory import ItemStack
from typing import Any

from jwcrate.api.models import Crate


class PreviewMenu:
    def __init__(self, crate: Crate, page: int = 0):
        self.crate = crate
        self.page = page
        from jwinventoryapi import Menu, MenuType
        self.menu = Menu(MenuType.DOUBLE_CHEST, f"Preview: {crate.name}")
        self.menu.set_locked(True)
        self._build()

    def _build(self):
        rewards = list(self.crate.rewards.values())
        start = self.page * 45
        end = start + 45
        page_rewards = rewards[start:end]

        for i, reward in enumerate(page_rewards):
            item = ItemStack(reward.preview.get("type", "minecraft:paper"), reward.preview.get("amount", 1))
            meta = item.item_meta
            if reward.preview.get("name"):
                meta.display_name = reward.preview["name"]
            if "lore" in reward.preview:
                meta.lore = reward.preview["lore"]
            if reward.preview.get("enchantments"):
                for ench_name, level in reward.preview["enchantments"].items():
                    meta.add_enchant(ench_name, level, True)
            item.set_item_meta(meta)
            self.menu.set_item(i, item)

        if self.page > 0:
            prev_item = ItemStack("minecraft:arrow")
            meta = prev_item.item_meta
            meta.display_name = "Previous Page"
            prev_item.set_item_meta(meta)
            self.menu.set_item(45, prev_item, on_click=self._on_prev)

        if end < len(rewards):
            next_item = ItemStack("minecraft:arrow")
            meta = next_item.item_meta
            meta.display_name = "Next Page"
            next_item.set_item_meta(meta)
            self.menu.set_item(53, next_item, on_click=self._on_next)

    def _on_prev(self, player: Player, slot: int, item: ItemStack, inv: Any):
        if self.page > 0:
            self.menu.close(player)
            PreviewMenu(self.crate, self.page - 1).open(player)

    def _on_next(self, player: Player, slot: int, item: ItemStack, inv: Any):
        self.menu.close(player)
        PreviewMenu(self.crate, self.page + 1).open(player)

    def open(self, player: Player):
        self.menu.send_to(player)
