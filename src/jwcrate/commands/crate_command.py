import time

from endstone import Player
from endstone.command import CommandSender, Command
from endstone.inventory import ItemStack
from endstone.plugin import Plugin

from jwcrate.api.models import Crate
from jwcrate.api.placeholder_handler import replace_placeholders
from jwcrate.crate.manager import CrateManager
from jwcrate.database.db import DatabaseManager
from jwcrate.api.economy_handler import EconomyHandler
from jwcrate.hologram.manager import HologramManager
from jwcrate.menu.edit import EditMenu
from jwcrate.menu.opening import CrateOpening
from jwcrate.menu.preview import PreviewMenu
from jwcrate.messages import msg


class CommandHandler:
    def __init__(self, plugin: Plugin, crate_manager: CrateManager, db: DatabaseManager, eco: EconomyHandler, hologram_manager: HologramManager = None):
        self.plugin = plugin
        self.crate_manager = crate_manager
        self.db = db
        self.eco = eco
        self.hologram_manager = hologram_manager
        self.setting_players: dict[str, str] = {}

    def handle(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not args:
            self._send_help(sender)
            return True

        sub = args[0].lower()

        if sub == "reload":
            return self._cmd_reload(sender)
        elif sub == "give":
            return self._cmd_give(sender, args)
        elif sub == "key":
            return self._handle_key(sender, args[1:])
        elif sub == "keygive":
            return self._handle_key(sender, ["give"] + args[1:])
        elif sub == "open":
            return self._cmd_open(sender, args)
        elif sub == "set":
            return self._cmd_set(sender, args)
        elif sub == "preview":
            return self._cmd_preview(sender, args)
        elif sub == "edit":
            return self._cmd_edit(sender, args)

        self._send_help(sender)
        return True

    def _cmd_reload(self, sender: CommandSender) -> bool:
        if not sender.has_permission("jwcrate.command.reload"):
            sender.send_message(msg("no_permission"))
            return True
        if self.hologram_manager:
            self.hologram_manager.remove_all_holograms()
        self.crate_manager.load_all()
        if self.hologram_manager:
            self.hologram_manager.spawn_all_holograms(self.crate_manager.crates)
        sender.send_message(msg("reload_success"))
        return True

    def _cmd_give(self, sender: CommandSender, args: list[str]) -> bool:
        if not sender.has_permission("jwcrate.command.give"):
            sender.send_message(msg("no_permission"))
            return True
        if len(args) < 3:
            sender.send_message(msg("usage_give"))
            return True

        player_name = args[1]
        crate_id = args[2]
        amount = int(args[3]) if len(args) > 3 else 1

        crate = self.crate_manager.get_crate(crate_id)
        if not crate:
            sender.send_message(msg("crate_not_found", crate=crate_id))
            return True

        target = self.plugin.server.get_player(player_name)
        if not target:
            sender.send_message(msg("player_not_found"))
            return True

        item = ItemStack(crate.item.get("type", "minecraft:chest"), amount)
        meta = item.item_meta
        if crate.item.get("name"):
            meta.display_name = crate.item["name"]
        item.set_item_meta(meta)
        target.inventory.add_item(item)
        sender.send_message(msg("give_crate_success", amount=amount, crate=crate.name, player=target.name))
        return True

    def _cmd_open(self, sender: CommandSender, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(msg("player_only"))
            return True
        if len(args) < 2:
            sender.send_message(msg("usage_open"))
            return True

        crate_id = args[1]
        crate = self.crate_manager.get_crate(crate_id)
        if not crate:
            sender.send_message(msg("crate_not_found", crate=crate_id))
            return True

        self.open_crate(sender, crate)
        return True

    def _cmd_set(self, sender: CommandSender, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(msg("player_only"))
            return True
        if not sender.has_permission("jwcrate.command.set"):
            sender.send_message(msg("no_permission"))
            return True
        if len(args) < 2:
            sender.send_message(msg("usage_set"))
            return True

        crate_id = args[1]
        crate = self.crate_manager.get_crate(crate_id)
        if not crate:
            sender.send_message(msg("crate_not_found", crate=crate_id))
            return True

        self.setting_players[sender.name] = crate_id
        sender.send_message(msg("set_instruction", crate=crate.name))
        return True

    def _cmd_preview(self, sender: CommandSender, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(msg("player_only"))
            return True
        if len(args) < 2:
            sender.send_message(msg("usage_preview"))
            return True

        crate_id = args[1]
        crate = self.crate_manager.get_crate(crate_id)
        if not crate:
            sender.send_message(msg("crate_not_found", crate=crate_id))
            return True

        PreviewMenu(crate).open(sender)
        return True

    def _cmd_edit(self, sender: CommandSender, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            sender.send_message(msg("player_only"))
            return True
        if not sender.has_permission("jwcrate.admin"):
            sender.send_message(msg("no_permission"))
            return True
        if len(args) < 2:
            sender.send_message(msg("usage_edit"))
            return True

        crate_id = args[1]
        crate = self.crate_manager.get_crate(crate_id)
        if not crate:
            sender.send_message(msg("crate_not_found", crate=crate_id))
            return True

        EditMenu(self.plugin, crate, self.crate_manager).open(sender)
        return True

    def _handle_key(self, sender: CommandSender, args: list[str]) -> bool:
        if not args:
            self._send_help(sender)
            return True

        sub = args[0].lower()
        if sub == "give":
            if not sender.has_permission("jwcrate.command.key.give"):
                sender.send_message(msg("no_permission"))
                return True
            if len(args) < 3:
                sender.send_message(msg("usage_key_give"))
                return True

            player_name = args[1]
            key_id = args[2]
            amount = int(args[3]) if len(args) > 3 else 1

            key = self.crate_manager.get_key(key_id)
            if not key:
                sender.send_message(msg("key_not_found", key=key_id))
                return True

            if key.virtual:
                self.db.add_key_balance(player_name, key.id, amount)
                sender.send_message(msg("give_virtual_key_success", amount=amount, key=key.name, player=player_name))
            else:
                target = self.plugin.server.get_player(player_name)
                if not target:
                    sender.send_message(msg("player_not_found"))
                    return True
                item = ItemStack(key.item.get("type", "minecraft:tripwire_hook"), amount)
                meta = item.item_meta
                if key.item.get("name"):
                    meta.display_name = key.item["name"]
                item.set_item_meta(meta)
                target.inventory.add_item(item)
                sender.send_message(msg("give_key_success", amount=amount, key=key.name, player=target.name))
            return True

        self._send_help(sender)
        return True

    def open_crate(self, player: Player, crate: Crate):
        if crate.permission_required and not player.has_permission(f"jwcrate.crate.{crate.id}"):
            player.send_message(msg("no_permission_crate"))
            return

        if crate.cooldown_enabled:
            current_time = time.time()
            cooldown_until = self.db.get_cooldown(player.name, crate.id)
            if current_time < cooldown_until:
                remain = int(cooldown_until - current_time)
                player.send_message(msg("cooldown", seconds=remain))
                return

        cost_met = False
        selected_cost = None
        for cost_id, cost in crate.costs.items():
            if not cost.required:
                cost_met = True
                break

            if cost.cost_type == "eco":
                if self.eco.get_balance(player.name, cost.currency_id or "coins") >= cost.amount:
                    cost_met = True
                    selected_cost = cost
                    break
            elif cost.cost_type == "key":
                key = self.crate_manager.get_key(cost.key_id)
                if not key:
                    continue
                if key.virtual:
                    if self.db.get_key_balance(player.name, key.id) >= cost.amount:
                        cost_met = True
                        selected_cost = cost
                        break
                else:
                    count = 0
                    for item in player.inventory.contents:
                        if item and item.type == key.item.get("type", "minecraft:tripwire_hook"):
                            if not key.item.get("name") or (item.item_meta and item.item_meta.display_name == key.item.get("name")):
                                count += item.amount
                    if count >= cost.amount:
                        cost_met = True
                        selected_cost = cost
                        break

        if not cost_met and crate.costs:
            player.send_message(msg("cannot_afford"))
            return

        if selected_cost:
            self._deduct_cost(player, selected_cost)

        if crate.cooldown_enabled and crate.cooldown_value > 0:
            self.db.set_cooldown(player.name, crate.id, time.time() + crate.cooldown_value)

        def on_finish(reward):
            self._give_reward(player, crate, reward)

        CrateOpening(self.plugin, crate, player, on_finish).start()

    def _deduct_cost(self, player: Player, cost):
        if cost.cost_type == "eco":
            self.eco.withdraw(player.name, cost.amount, cost.currency_id or "coins")
        elif cost.cost_type == "key":
            key = self.crate_manager.get_key(cost.key_id)
            if key.virtual:
                self.db.remove_key_balance(player.name, key.id, int(cost.amount))
            else:
                remain = int(cost.amount)
                for i, item in enumerate(player.inventory.contents):
                    if remain <= 0:
                        break
                    if item and item.type == key.item.get("type", "minecraft:tripwire_hook"):
                        if not key.item.get("name") or (item.item_meta and item.item_meta.display_name == key.item.get("name")):
                            take = min(item.amount, remain)
                            remain -= take
                            if item.amount - take <= 0:
                                player.inventory.clear(i)
                            else:
                                item.amount -= take
                                player.inventory.set_item(i, item)

    def _give_reward(self, player: Player, crate: Crate, reward):
        if reward.broadcast:
            self.plugin.server.broadcast_message(msg("reward_broadcast", player=player.name, reward=reward.name, crate=crate.name))
        else:
            player.send_message(msg("reward_win", reward=reward.name))

        if reward.type == "ITEM":
            for r_item in reward.items:
                item = ItemStack(r_item.get("type", "minecraft:diamond"), r_item.get("amount", 1))
                meta = item.item_meta
                if r_item.get("name"):
                    meta.display_name = r_item["name"]
                if r_item.get("lore"):
                    meta.lore = r_item["lore"]
                if r_item.get("enchantments"):
                    for ench_name, level in r_item["enchantments"].items():
                        meta.add_enchant(ench_name, level, True)
                if r_item.get("unbreakable"):
                    meta.is_unbreakable = True
                item.set_item_meta(meta)
                player.inventory.add_item(item)
        elif reward.type == "COMMAND":
            for cmd in reward.commands:
                cmd = replace_placeholders(cmd, player)
                self.plugin.server.dispatch_command(self.plugin.server.command_sender, cmd)

    def _send_help(self, sender: CommandSender):
        sender.send_message(msg("help_header"))
        sender.send_message(msg("help_reload"))
        sender.send_message(msg("help_give"))
        sender.send_message(msg("help_key_give"))
        sender.send_message(msg("help_open"))
        sender.send_message(msg("help_preview"))
        sender.send_message(msg("help_edit"))
        sender.send_message(msg("help_set"))
