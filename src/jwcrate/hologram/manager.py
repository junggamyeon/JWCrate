import random
from typing import Dict, Set, Tuple
from binarystream import BinaryStream
from endstone import Logger
from endstone.plugin import Plugin
from endstone.event import event_handler, EventPriority
from endstone.event import PlayerJoinEvent

from jwcrate.api.models import Crate

HOLOGRAM_TAG = "jwcrate_hologram"


class HologramEntity:
    """Represents a client-side floating text entity."""

    def __init__(self, text: str, x: float, y: float, z: float, dim: int):
        self.runtime_id = random.randint(10000000, 100000000)
        self.text = text
        self.x = x
        self.y = y
        self.z = z
        self.dim = dim


class HologramManager:
    """Manages floating text holograms above crate locations using client-side packets."""

    def __init__(self, plugin: Plugin, logger: Logger):
        self.plugin = plugin
        self.logger = logger
        # All active holograms: key = (x, y, z, dim_name), value = HologramEntity
        self.holograms: Dict[Tuple[float, float, float, str], HologramEntity] = {}
        # Track which holograms each player has seen: player_uuid -> set of runtime_ids
        self.player_cache: Dict[str, Set[int]] = {}
        self._task = None

    def _dim_name_to_id(self, dim_name: str) -> int:
        """Convert dimension name to numeric ID."""
        dim_lower = dim_name.lower()
        if "nether" in dim_lower:
            return 1
        elif "end" in dim_lower or "the_end" in dim_lower:
            return 2
        return 0  # Overworld

    def _build_spawn_packet(self, hologram: HologramEntity) -> bytes:
        """Build an AddEntityPacket for a floating text hologram."""
        s = BinaryStream()
        s.write_varint64(hologram.runtime_id)
        s.write_unsigned_varint64(hologram.runtime_id)
        s.write_signed_short(28678)
        s.write_signed_int(1702453612)
        s.write_byte(114)
        s.write_float(hologram.x)
        s.write_float(hologram.y)
        s.write_float(hologram.z)
        s.write_unsigned_int64(0)
        s.write_signed_int64(0)
        s.write_unsigned_int64(0)
        s.write_signed_int(0)
        s.write_signed_big_endian_int(590852)
        s.write_string(hologram.text)
        s.write_unsigned_int64(22799473113563942)
        s.write_signed_int64(6491382630230130945)
        s.write_unsigned_int64(144442844453603100)
        s.write_signed_int64(147508270825868034)
        s.write_unsigned_int64(53750529787)
        return s.get_and_release_data()

    def _build_remove_packet(self, runtime_id: int) -> bytes:
        """Build a RemoveEntityPacket."""
        s = BinaryStream()
        s.write_varint64(runtime_id)
        return s.get_and_release_data()

    def _send_holograms_to_players(self):
        """Send/update holograms to all online players based on their dimension."""
        try:
            for player in self.plugin.server.online_players:
                player_dim = player.location.dimension.type.value
                uid = str(player.unique_id)

                if uid not in self.player_cache:
                    self.player_cache[uid] = set()

                for key, hologram in self.holograms.items():
                    if hologram.dim == player_dim:
                        # Send spawn packet
                        data = self._build_spawn_packet(hologram)
                        player.send_packet(13, data)
                        self.player_cache[uid].add(hologram.runtime_id)
                    else:
                        # Remove if player changed dimension
                        if hologram.runtime_id in self.player_cache[uid]:
                            data = self._build_remove_packet(hologram.runtime_id)
                            player.send_packet(14, data)
                            self.player_cache[uid].discard(hologram.runtime_id)
        except Exception as e:
            self.logger.error(f"Error sending holograms: {e}")

    def start_task(self):
        """Start the repeating task to send holograms to players."""
        if self._task is None:
            self._task = self.plugin.server.scheduler.run_task(
                self.plugin, self._send_holograms_to_players, delay=0, period=40
            )

    def stop_task(self):
        """Stop the repeating task."""
        if self._task:
            self._task.cancel()
            self._task = None

    def spawn_hologram(self, crate: Crate, x: float, y: float, z: float, dim_name: str):
        """Register a hologram for a crate location."""
        # Use custom hologram text from config, fallback to crate name
        hologram_text = crate.hologram if crate.hologram else crate.name
        height = crate.hologram_height if crate.hologram_height else 1.5

        key = (x, y, z, dim_name)
        dim_id = self._dim_name_to_id(dim_name)

        # Position centered on block, height offset above
        hologram = HologramEntity(
            text=hologram_text,
            x=x + 0.5,
            y=y + height,
            z=z + 0.5,
            dim=dim_id
        )
        self.holograms[key] = hologram
        self.logger.info(f"Registered hologram for '{crate.name}' at {x}, {y}, {z}")

    def remove_hologram(self, x: float, y: float, z: float, dim_name: str):
        """Remove a hologram at the given location."""
        key = (x, y, z, dim_name)
        hologram = self.holograms.pop(key, None)
        if hologram:
            # Send remove packet to all online players
            try:
                data = self._build_remove_packet(hologram.runtime_id)
                for player in self.plugin.server.online_players:
                    player.send_packet(14, data)
                    uid = str(player.unique_id)
                    if uid in self.player_cache:
                        self.player_cache[uid].discard(hologram.runtime_id)
            except Exception as e:
                self.logger.error(f"Error removing hologram: {e}")

    def spawn_all_holograms(self, crates: Dict[str, Crate]):
        """Register holograms for all crate locations and start the update task."""
        for crate in crates.values():
            for loc in crate.locations:
                self.spawn_hologram(
                    crate,
                    loc["x"], loc["y"], loc["z"],
                    loc.get("dim", "")
                )
        self.start_task()

    def remove_all_holograms(self):
        """Remove all holograms and stop the update task."""
        self.stop_task()
        try:
            for hologram in self.holograms.values():
                data = self._build_remove_packet(hologram.runtime_id)
                for player in self.plugin.server.online_players:
                    player.send_packet(14, data)
        except Exception as e:
            self.logger.error(f"Error removing all holograms: {e}")
        self.holograms.clear()
        self.player_cache.clear()
