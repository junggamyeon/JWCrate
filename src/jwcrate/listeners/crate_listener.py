from endstone import ColorFormat
from endstone.event import event_handler, EventPriority
from endstone.event import PlayerInteractEvent, BlockBreakEvent
from jwcrate.crate.manager import CrateManager
from jwcrate.commands.crate_command import CommandHandler
from jwcrate.hologram.manager import HologramManager
from jwcrate.menu.preview import PreviewMenu
from endstone.plugin import Plugin

class CrateListener:
    def __init__(self, plugin: Plugin, crate_manager: CrateManager, command_handler: CommandHandler, hologram_manager: HologramManager):
        self.plugin = plugin
        self.crate_manager = crate_manager
        self.command_handler = command_handler
        self.hologram_manager = hologram_manager

    @event_handler(priority=EventPriority.NORMAL)
    def on_player_interact(self, event: PlayerInteractEvent):
        player = event.player
        block = event.block
        
        # Handle "set" mode: player right-clicks a block after /jwcrate set <id>
        if player.name in self.command_handler.setting_players:
            if not block:
                return
            event.is_cancelled = True
            crate_id = self.command_handler.setting_players.pop(player.name)
            crate = self.crate_manager.get_crate(crate_id)
            if not crate:
                player.send_message(f"{ColorFormat.RED}Crate '{crate_id}' no longer exists.")
                return
            
            x = block.location.x
            y = block.location.y
            z = block.location.z
            dim = block.location.dimension.name
            
            crate.locations.append({
                "x": x,
                "y": y,
                "z": z,
                "dim": dim
            })
            self.crate_manager.save_crate_locations(crate)
            
            # Spawn hologram above the crate
            self.hologram_manager.spawn_hologram(crate, x, y, z, dim)
            
            player.send_message(f"{ColorFormat.GREEN}Crate location for '{crate.name}' set successfully!")
            return

        if not block:
            return
            
        crate = self.crate_manager.get_crate_by_location(
            block.location.x, block.location.y, block.location.z, block.location.dimension.name
        )
        
        if crate:
            event.is_cancelled = True
            if player.is_sneaking:
                menu = PreviewMenu(crate)
                menu.open(player)
            else:
                self.command_handler.open_crate(player, crate)

    @event_handler(priority=EventPriority.NORMAL)
    def on_block_break(self, event: BlockBreakEvent):
        block = event.block
        if not block:
            return
            
        crate = self.crate_manager.get_crate_by_location(
            block.location.x, block.location.y, block.location.z, block.location.dimension.name
        )
        
        if crate:
            if not event.player.has_permission("jwcrate.admin"):
                event.player.send_message(f"{ColorFormat.RED}You cannot break a crate block.")
                event.is_cancelled = True
                return
            
            x = block.location.x
            y = block.location.y
            z = block.location.z
            dim = block.location.dimension.name
            
            # Remove hologram
            self.hologram_manager.remove_hologram(x, y, z, dim)
                
            event.player.send_message(f"{ColorFormat.YELLOW}Crate block removed.")
            crate.locations = [loc for loc in crate.locations if not (
                loc["x"] == x and
                loc["y"] == y and
                loc["z"] == z and
                loc.get("dim", "") == dim
            )]
            self.crate_manager.save_crate_locations(crate)
