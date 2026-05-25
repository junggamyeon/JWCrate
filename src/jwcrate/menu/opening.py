import random
from typing import Callable

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
        self.max_ticks = 60
        self.menu = None
        self.total_weight = sum(r.weight for r in self.rewards)
        if self.total_weight <= 0:
            self.total_weight = 1
        # Track which reward is in each slot of the rolling row
        self._slot_rewards: list[Reward] = []

    def _random_reward(self) -> Reward:
        if not self.rewards:
            return None
        r = random.uniform(0, self.total_weight)
        cumulative = 0.0
        for reward in self.rewards:
            cumulative += reward.weight
            if r <= cumulative:
                return reward
        return self.rewards[-1]

    def _reward_item(self, reward: Reward) -> ItemStack:
        if not reward:
            return ItemStack("minecraft:barrier", 1)
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
        return item

    def _glass(self, color: str = "minecraft:yellow_stained_glass_pane") -> ItemStack:
        return ItemStack(color, 1)

    def start(self):
        if not self.crate.opening_enabled or not self.rewards:
            reward = self._random_reward()
            if reward:
                self.on_finish(reward)
            return

        from jwinventoryapi import Menu, MenuType
        self.menu = Menu(MenuType.CHEST, f"Opening {self.crate.name}")
        self.menu.set_locked(True)

        inv = self.menu.inventory
        inv.begin_batch()

        for i in [0, 1, 2, 3, 5, 6, 7, 8, 18, 19, 20, 21, 23, 24, 25, 26]:
            inv.set_item(i, self._glass())
        inv.set_item(4, self._glass("minecraft:red_stained_glass_pane"))
        inv.set_item(22, self._glass("minecraft:red_stained_glass_pane"))

        # Fill rolling row (slots 9-17) with random rewards and track them
        self._slot_rewards = []
        for i in range(9, 18):
            reward = self._random_reward()
            self._slot_rewards.append(reward)
            inv.set_item(i, self._reward_item(reward))

        inv._dirty_slots.clear()
        inv._batch_mode = False

        self.menu.send_to(self.player)
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

            inv = self.menu.inventory
            inv.begin_batch()

            # Shift rewards left
            self._slot_rewards.pop(0)
            new_reward = self._random_reward()
            self._slot_rewards.append(new_reward)

            for i in range(9):
                inv.set_item(9 + i, self._reward_item(self._slot_rewards[i]))

            inv._dirty_slots.clear()
            inv._batch_mode = False

            self.menu.refresh_contents()

        except Exception:
            self._cancel()

    def _finish(self):
        self._cancel()
        try:
            if not self.player or not self.player.is_valid:
                return

            # The winner is whatever is at the center slot (index 4 in the row = slot 13)
            winning_reward = self._slot_rewards[4]

            inv = self.menu.inventory
            inv.begin_batch()
            inv.set_item(13, self._reward_item(winning_reward))
            inv.set_item(4, self._glass("minecraft:lime_stained_glass_pane"))
            inv.set_item(22, self._glass("minecraft:lime_stained_glass_pane"))
            inv._dirty_slots.clear()
            inv._batch_mode = False

            self.menu.refresh_contents()

            def close_and_reward():
                try:
                    if self.player and self.player.is_valid:
                        self.menu.close(self.player)
                        if winning_reward:
                            self.on_finish(winning_reward)
                except Exception:
                    pass

            self.plugin.server.scheduler.run_task(self.plugin, close_and_reward, delay=30)
        except Exception:
            pass

    def _cancel(self):
        if self.task:
            self.task.cancel()
            self.task = None
