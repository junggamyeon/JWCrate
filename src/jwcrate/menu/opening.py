import random
from typing import Callable, Any

from endstone import Player
from endstone.inventory import ItemStack
from endstone.plugin import Plugin

from jwcrate.api.models import Crate, Reward


class CrateOpening:
    def __init__(self, plugin: Plugin, crate: Crate, player: Player, on_finish: Callable[[Reward], None]):
        self.plugin = plugin
        self.crate = crate
        self.player = player
        self.on_finish = on_finish
        self.rewards = list(crate.rewards.values())
        self.task = None
        self.ticks = 0
        self.max_ticks = 60  # 3 seconds at 4-tick intervals
        self.final_reward = None
        self.menu = None

        self.total_weight = sum(r.weight for r in self.rewards)
        if self.total_weight <= 0:
            self.total_weight = 1

    def _get_random_reward(self) -> Reward:
        if not self.rewards:
            return None
        r = random.uniform(0, self.total_weight)
        cumulative = 0.0
        for reward in self.rewards:
            cumulative += reward.weight
            if r <= cumulative:
                return reward
        return self.rewards[-1]

    def _reward_to_itemstack(self, reward: Reward) -> ItemStack:
        if not reward:
            return ItemStack("minecraft:barrier", 1)
        item = ItemStack(reward.preview.get("type", "minecraft:paper"), reward.preview.get("amount", 1))
        meta = item.item_meta
        if reward.preview.get("name"):
            meta.display_name = reward.preview.get("name")
        if "lore" in reward.preview:
            meta.lore = reward.preview["lore"]
        item.set_item_meta(meta)
        return item

    def _make_glass(self, color: str = "minecraft:yellow_stained_glass_pane") -> ItemStack:
        return ItemStack(color, 1)

    def start(self):
        if not self.crate.opening_enabled or not self.rewards:
            reward = self._get_random_reward()
            if reward:
                self.on_finish(reward)
            return

        self.final_reward = self._get_random_reward()

        from jwinventoryapi import Menu, MenuType
        self.menu = Menu(MenuType.CHEST, f"Opening {self.crate.name}")
        self.menu.set_locked(True)

        # Build initial layout in batch mode (no per-slot packets)
        inv = self.menu.inventory
        inv.begin_batch()

        for i in [0, 1, 2, 3, 5, 6, 7, 8, 18, 19, 20, 21, 23, 24, 25, 26]:
            inv.set_item(i, self._make_glass())
        inv.set_item(4, self._make_glass("minecraft:red_stained_glass_pane"))
        inv.set_item(22, self._make_glass("minecraft:red_stained_glass_pane"))

        for i in range(9, 18):
            inv.set_item(i, self._reward_to_itemstack(self._get_random_reward()))

        inv.end_batch()

        self.menu.send_to(self.player)

        # Start animation after menu is fully open (20 ticks = 1s delay)
        # period=4 ticks (0.2s per frame)
        self.task = self.plugin.server.scheduler.run_task(self.plugin, self._tick, delay=20, period=4)

    def _tick(self):
        try:
            if not self.player or not self.player.is_valid:
                self._cancel()
                return

            self.ticks += 4

            if self.ticks >= self.max_ticks:
                self._finish()
                return

            # Batch update: shift items left, add new on right
            inv = self.menu.inventory
            inv.begin_batch()

            for i in range(9, 17):
                next_item = inv.get_item(i + 1)
                if next_item:
                    inv.set_item(i, next_item)

            if self.ticks >= self.max_ticks - 8:
                inv.set_item(17, self._reward_to_itemstack(self.final_reward))
            else:
                inv.set_item(17, self._reward_to_itemstack(self._get_random_reward()))

            inv.end_batch()

            # Send full contents once per tick instead of per-slot packets
            self.menu.refresh_contents()

        except Exception:
            self._cancel()

    def _finish(self):
        self._cancel()

        try:
            if not self.player or not self.player.is_valid:
                return

            inv = self.menu.inventory
            inv.begin_batch()
            inv.set_item(13, self._reward_to_itemstack(self.final_reward))
            inv.set_item(4, self._make_glass("minecraft:lime_stained_glass_pane"))
            inv.set_item(22, self._make_glass("minecraft:lime_stained_glass_pane"))
            inv.end_batch()

            self.menu.refresh_contents()

            # Close and give reward after 1.5 seconds
            self.plugin.server.scheduler.run_task(self.plugin, self._close_and_reward, delay=30)
        except Exception:
            pass

    def _close_and_reward(self):
        try:
            if self.player and self.player.is_valid:
                self.menu.close(self.player)
                if self.final_reward:
                    self.on_finish(self.final_reward)
        except Exception:
            pass

    def _cancel(self):
        if self.task:
            self.task.cancel()
            self.task = None
