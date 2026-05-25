from endstone.plugin import Plugin
from endstone.command import Command, CommandSender

from jwcrate.crate.manager import CrateManager
from jwcrate.database.db import DatabaseManager
from jwcrate.api.economy_handler import EconomyHandler
from jwcrate.commands.crate_command import CommandHandler
from jwcrate.listeners.crate_listener import CrateListener
from jwcrate.hologram.manager import HologramManager
from jwcrate.messages import load_messages


class JWCrate(Plugin):
    prefix = "JWCrate"
    api_version = "0.6"
    load = "POSTWORLD"

    commands = {
        "jwcrate": {
            "description": "Main command for JWCrate",
            "usages": [
                "/jwcrate",
                "/jwcrate reload",
                "/jwcrate give <player: player> <crate: string> [amount: int]",
                "/jwcrate keygive <target: player> <key: string> [quantity: int]",
                "/jwcrate set <crate: string>",
                "/jwcrate open <crate: string>",
                "/jwcrate preview <crate: string>",
                "/jwcrate edit <crate: string>"
            ],
            "aliases": ["crate", "crates"]
        }
    }

    permissions = {
        "jwcrate.command.reload": {"description": "Allows reloading crates config", "default": "op"},
        "jwcrate.command.give": {"description": "Allows giving physical crates", "default": "op"},
        "jwcrate.command.key.give": {"description": "Allows giving keys", "default": "op"},
        "jwcrate.command.set": {"description": "Allows setting crate blocks", "default": "op"},
        "jwcrate.admin": {
            "description": "Admin permissions for JWCrate",
            "default": "op",
            "children": {
                "jwcrate.command.reload": True,
                "jwcrate.command.give": True,
                "jwcrate.command.key.give": True,
                "jwcrate.command.set": True
            }
        }
    }

    def on_enable(self) -> None:
        load_messages(self.data_folder)
        self.db_manager = DatabaseManager(self.data_folder)
        self.crate_manager = CrateManager(self.data_folder, self.logger)
        self.crate_manager.load_all()
        self.eco_handler = EconomyHandler(self.logger)
        self.hologram_manager = HologramManager(self, self.logger)
        self.command_handler = CommandHandler(self, self.crate_manager, self.db_manager, self.eco_handler, self.hologram_manager)
        self.listener = CrateListener(self, self.crate_manager, self.command_handler, self.hologram_manager)
        self.register_events(self.listener)
        self.server.scheduler.run_task(self, self._spawn_holograms, delay=40)
        self.logger.info("JWCrate enabled.")

    def _spawn_holograms(self):
        self.hologram_manager.spawn_all_holograms(self.crate_manager.crates)

    def on_disable(self) -> None:
        self.hologram_manager.remove_all_holograms()

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if command.name == "jwcrate":
            return self.command_handler.handle(sender, command, args)
        return False
