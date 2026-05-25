from endstone import Player
from endstone.inventory import ItemStack
from typing import Callable, List, Any
from jwcrate.api.models import Crate

class PreviewMenu:
    def __init__(self, crate: Crate, page: int = 0):
        self.crate = crate
        self.page = page
        from jwinventoryapi import Menu, MenuType
        self.menu = Menu(MenuType.DOUBLE_CHEST, f"Preview: {crate.name}")
        self._build_menu()

    def _build_menu(self):
        rewards = list(self.crate.rewards.values())
        start_idx = self.page * 45
        end_idx = start_idx + 45
        page_rewards = rewards[start_idx:end_idx]
        
        for i, reward in enumerate(page_rewards):
            item = ItemStack(reward.preview.get("type", "minecraft:paper"), reward.preview.get("amount", 1))
            meta = item.item_meta
            if reward.preview.get("name"):
                meta.display_name = reward.preview.get("name")
            if "lore" in reward.preview:
                meta.lore = reward.preview["lore"]
            item.set_item_meta(meta)
            self.menu.set_item(i, item)
            
        # Add next/prev buttons on row 6 if needed (index 45-53)
        if self.page > 0:
            prev_item = ItemStack("minecraft:arrow")
            meta = prev_item.item_meta
            meta.display_name = "Previous Page"
            prev_item.set_item_meta(meta)
            self.menu.set_item(45, prev_item, on_click=self.on_prev_click)
            
        if end_idx < len(rewards):
            next_item = ItemStack("minecraft:arrow")
            meta = next_item.item_meta
            meta.display_name = "Next Page"
            next_item.set_item_meta(meta)
            self.menu.set_item(53, next_item, on_click=self.on_next_click)

    def on_prev_click(self, player: Player, slot: int, item: ItemStack, inv: Any):
        if self.page > 0:
            new_menu = PreviewMenu(self.crate, self.page - 1)
            self.menu.close(player)
            new_menu.open(player)

    def on_next_click(self, player: Player, slot: int, item: ItemStack, inv: Any):
        new_menu = PreviewMenu(self.crate, self.page + 1)
        self.menu.close(player)
        new_menu.open(player)

    def open(self, player: Player):
        self.menu.send_to(player)
