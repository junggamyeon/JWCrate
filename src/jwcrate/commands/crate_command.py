import time
from typing import Optional, List

from endstone import Player, ColorFormat
from endstone.command import CommandSender, Command
from endstone.plugin import Plugin

from jwcrate.api.models import Crate, CrateKey
from jwcrate.crate.manager import CrateManager
from jwcrate.database.db import DatabaseManager
from jwcrate.api.economy_handler import EconomyHandler
from jwcrate.api.placeholder_handler import replace_placeholders
from jwcrate.menu.preview import PreviewMenu
from jwcrate.menu.opening import CrateOpening
from jwcrate.menu.edit import EditMenu
from jwcrate.hologram.manager import HologramManager
from endstone.inventory import ItemStack

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
            if not sender.has_permission("jwcrate.command.reload"):
                sender.send_message(f"{ColorFormat.RED}No permission.")
                return True
            # Remove old holograms, reload config, respawn holograms
            if self.hologram_manager:
                self.hologram_manager.remove_all_holograms()
            self.crate_manager.load_all()
            if self.hologram_manager:
                self.hologram_manager.spawn_all_holograms(self.crate_manager.crates)
            sender.send_message(f"{ColorFormat.GREEN}Reloaded crates and keys.")
            return True

        if sub == "give":
            # /jwcrate give <player> <crate_id> [amount]
            if not sender.has_permission("jwcrate.command.give"):
                sender.send_message(f"{ColorFormat.RED}No permission.")
                return True
            if len(args) < 3:
                sender.send_message(f"{ColorFormat.RED}Usage: /jwcrate give <player> <crate_id> [amount]")
                return True
            player_name = args[1]
            crate_id = args[2]
            amount = int(args[3]) if len(args) > 3 else 1
            
            crate = self.crate_manager.get_crate(crate_id)
            if not crate:
                sender.send_message(f"{ColorFormat.RED}Crate '{crate_id}' not found.")
                return True
                
            target = self.plugin.server.get_player(player_name)
            if not target:
                sender.send_message(f"{ColorFormat.RED}Player not found.")
                return True
                
            item = ItemStack(crate.item.get("type", "minecraft:chest"), amount)
            meta = item.item_meta
            if crate.item.get("name"):
                meta.display_name = crate.item.get("name")
            item.set_item_meta(meta)
            # Add crate id as custom data if needed, Endstone might support custom NBT or we just match by name
            # For simplicity, we just give the item.
            target.inventory.add_item(item)
            sender.send_message(f"{ColorFormat.GREEN}Gave {amount} {crate.name} to {target.name}.")
            return True

        if sub == "key":
            return self._handle_key(sender, args[1:])

        if sub == "keygive":
            return self._handle_key(sender, ["give"] + args[1:])

        if sub == "open":
            # /jwcrate open <crate_id>
            if not isinstance(sender, Player):
                sender.send_message(f"{ColorFormat.RED}Player only command.")
                return True
            if len(args) < 2:
                sender.send_message(f"{ColorFormat.RED}Usage: /jwcrate open <crate_id>")
                return True
            crate_id = args[1]
            crate = self.crate_manager.get_crate(crate_id)
            if not crate:
                sender.send_message(f"{ColorFormat.RED}Crate '{crate_id}' not found.")
                return True
                
            self.open_crate(sender, crate)
            return True

        if sub == "set":
            if not isinstance(sender, Player):
                sender.send_message(f"{ColorFormat.RED}Player only command.")
                return True
            if not sender.has_permission("jwcrate.command.set"):
                sender.send_message(f"{ColorFormat.RED}No permission.")
                return True
            if len(args) < 2:
                sender.send_message(f"{ColorFormat.RED}Usage: /jwcrate set <crate_id>")
                return True
            
            crate_id = args[1]
            crate = self.crate_manager.get_crate(crate_id)
            if not crate:
                sender.send_message(f"{ColorFormat.RED}Crate '{crate_id}' not found.")
                return True
            
            self.setting_players[sender.name] = crate_id
            sender.send_message(f"{ColorFormat.GREEN}Right-click a block to set the crate location for '{crate.name}'.")
            return True

        if sub == "preview":
            if not isinstance(sender, Player):
                sender.send_message(f"{ColorFormat.RED}Player only command.")
                return True
            if len(args) < 2:
                sender.send_message(f"{ColorFormat.RED}Usage: /jwcrate preview <crate_id>")
                return True
            crate_id = args[1]
            crate = self.crate_manager.get_crate(crate_id)
            if not crate:
                sender.send_message(f"{ColorFormat.RED}Crate '{crate_id}' not found.")
                return True
                
            menu = PreviewMenu(crate)
            menu.open(sender)
            return True

        if sub == "edit":
            if not isinstance(sender, Player):
                sender.send_message(f"{ColorFormat.RED}Player only command.")
                return True
            if not sender.has_permission("jwcrate.admin"):
                sender.send_message(f"{ColorFormat.RED}No permission.")
                return True
            if len(args) < 2:
                sender.send_message(f"{ColorFormat.RED}Usage: /jwcrate edit <crate_id>")
                return True
            crate_id = args[1]
            crate = self.crate_manager.get_crate(crate_id)
            if not crate:
                sender.send_message(f"{ColorFormat.RED}Crate '{crate_id}' not found.")
                return True

            edit_menu = EditMenu(self.plugin, crate, self.crate_manager)
            edit_menu.open(sender)
            return True

        self._send_help(sender)
        return True

    def _handle_key(self, sender: CommandSender, args: list[str]) -> bool:
        if not args:
            self._send_help(sender)
            return True
            
        sub = args[0].lower()
        if sub == "give":
            # /jwcrate key give <player> <key_id> [amount]
            if not sender.has_permission("jwcrate.command.key.give"):
                sender.send_message(f"{ColorFormat.RED}No permission.")
                return True
            if len(args) < 3:
                sender.send_message(f"{ColorFormat.RED}Usage: /jwcrate key give <player> <key_id> [amount]")
                return True
            player_name = args[1]
            key_id = args[2]
            amount = int(args[3]) if len(args) > 3 else 1
            
            key = self.crate_manager.get_key(key_id)
            if not key:
                sender.send_message(f"{ColorFormat.RED}Key '{key_id}' not found.")
                return True
                
            if key.virtual:
                self.db.add_key_balance(player_name, key.id, amount)
                sender.send_message(f"{ColorFormat.GREEN}Gave {amount} virtual {key.name} to {player_name}.")
            else:
                target = self.plugin.server.get_player(player_name)
                if not target:
                    sender.send_message(f"{ColorFormat.RED}Player not found for physical key.")
                    return True
                item = ItemStack(key.item.get("type", "minecraft:tripwire_hook"), amount)
                meta = item.item_meta
                if key.item.get("name"):
                    meta.display_name = key.item.get("name")
                item.set_item_meta(meta)
                target.inventory.add_item(item)
                sender.send_message(f"{ColorFormat.GREEN}Gave {amount} {key.name} to {target.name}.")
            return True
            
        self._send_help(sender)
        return True

    def open_crate(self, player: Player, crate: Crate):
        if crate.permission_required and not player.has_permission(f"jwcrate.crate.{crate.id}"):
            player.send_message(f"{ColorFormat.RED}You don't have permission to open this crate.")
            return

        if crate.cooldown_enabled:
            current_time = time.time()
            cooldown_until = self.db.get_cooldown(player.name, crate.id)
            if current_time < cooldown_until:
                remain = int(cooldown_until - current_time)
                player.send_message(f"{ColorFormat.RED}Crate is on cooldown for {remain}s.")
                return

        # Check costs
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
                    # Physical key
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
            player.send_message(f"{ColorFormat.RED}You cannot afford to open this crate.")
            return

        # Deduct cost
        if selected_cost:
            if selected_cost.cost_type == "eco":
                self.eco.withdraw(player.name, selected_cost.amount, selected_cost.currency_id or "coins")
            elif selected_cost.cost_type == "key":
                key = self.crate_manager.get_key(selected_cost.key_id)
                if key.virtual:
                    self.db.remove_key_balance(player.name, key.id, int(selected_cost.amount))
                else:
                    remain = int(selected_cost.amount)
                    # Removing physical items from inventory
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

        if crate.cooldown_enabled and crate.cooldown_value > 0:
            self.db.set_cooldown(player.name, crate.id, time.time() + crate.cooldown_value)

        # Start opening
        def on_finish(reward):
            self.give_reward(player, crate, reward)

        opening = CrateOpening(self.plugin, crate, player, on_finish)
        opening.start()

    def give_reward(self, player: Player, crate: Crate, reward):
        if reward.broadcast:
            self.plugin.server.broadcast_message(f"{ColorFormat.GOLD}{player.name} won {reward.id} from {crate.name}!")
        else:
            player.send_message(f"{ColorFormat.GREEN}You won {reward.id}!")
            
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
                    meta.set_unbreakable(True)
                item.set_item_meta(meta)
                player.inventory.add_item(item)
        elif reward.type == "COMMAND":
            for cmd in reward.commands:
                cmd = replace_placeholders(cmd, player)
                self.plugin.server.dispatch_command(self.plugin.server.command_sender, cmd)

    def _send_help(self, sender: CommandSender):
        sender.send_message(f"{ColorFormat.YELLOW}--- JWCrate Help ---")
        sender.send_message(f"/jwcrate reload - Reload config")
        sender.send_message(f"/jwcrate give <player> <crate> [amount] - Give physical crate")
        sender.send_message(f"/jwcrate key give <player> <key> [amount] - Give key")
        sender.send_message(f"/jwcrate open <crate> - Open crate virtually")
        sender.send_message(f"/jwcrate preview <crate> - Preview crate")
        sender.send_message(f"/jwcrate edit <crate> - Edit crate rewards")
        sender.send_message(f"/jwcrate set <crate> - Set crate block location")
