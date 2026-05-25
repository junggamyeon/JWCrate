import os
from pathlib import Path
from typing import Dict, List, Optional
from endstone import Logger
from endstone import Player

from jwcrate.api.models import Crate, CrateKey, Reward, CrateCost
from jwcrate.utils.config_loader import load_yaml, save_yaml

class CrateManager:
    def __init__(self, data_folder: Path, logger: Logger):
        self.data_folder = data_folder
        self.logger = logger
        self.crates: Dict[str, Crate] = {}
        self.keys: Dict[str, CrateKey] = {}

    def load_all(self):
        self.crates.clear()
        self.keys.clear()
        self._load_keys()
        self._load_crates()

    def _load_keys(self):
        keys_dir = self.data_folder / "keys"
        keys_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default key if empty
        if not any(keys_dir.iterdir()):
            default_key = {
                "Name": "Default Key",
                "Virtual": False,
                "ItemData": {
                    "type": "minecraft:tripwire_hook",
                    "name": "Default Key"
                }
            }
            save_yaml(keys_dir / "default.yml", default_key)

        for file in keys_dir.glob("*.yml"):
            try:
                data = load_yaml(file)
                key_id = file.stem
                self.keys[key_id] = CrateKey(
                    id=key_id,
                    name=data.get("Name", key_id),
                    virtual=data.get("Virtual", False),
                    item=data.get("ItemData", {"type": "minecraft:tripwire_hook", "name": key_id})
                )
            except Exception as e:
                self.logger.error(f"Failed to load key {file.name}: {e}")

    def _load_crates(self):
        crates_dir = self.data_folder / "crates"
        crates_dir.mkdir(parents=True, exist_ok=True)

        if not any(crates_dir.iterdir()):
            self._create_default_crate(crates_dir)

        for file in crates_dir.glob("*.yml"):
            try:
                data = load_yaml(file)
                crate_id = file.stem
                
                costs = {}
                for cid, cdata in data.get("CostOptions", {}).items():
                    costs[cid] = CrateCost(
                        id=cid,
                        required=cdata.get("required", True),
                        name=cdata.get("name", "Cost"),
                        cost_type=cdata.get("type", "key"),
                        currency_id=cdata.get("currency_id", None),
                        key_id=cdata.get("key_id", None),
                        amount=cdata.get("amount", 1.0)
                    )

                rewards = {}
                for rid, rdata in data.get("Rewards", {}).get("List", {}).items():
                    rewards[rid] = Reward(
                        id=rid,
                        type=rdata.get("Type", "ITEM"),
                        weight=rdata.get("Weight", 10.0),
                        rarity=rdata.get("Rarity", "common"),
                        preview=rdata.get("PreviewData", {"type": "minecraft:paper"}),
                        items=rdata.get("ItemsData", []),
                        commands=rdata.get("Commands", []),
                        broadcast=rdata.get("Broadcast", False)
                    )

                self.crates[crate_id] = Crate(
                    id=crate_id,
                    name=data.get("Name", crate_id),
                    description=data.get("Description", []),
                    item=data.get("ItemProvider", {"type": "minecraft:chest", "name": crate_id}),
                    preview_enabled=data.get("Preview", {}).get("Enabled", True),
                    opening_enabled=data.get("Animation", {}).get("Enabled", True),
                    cooldown_enabled=data.get("OpeningCooldown", {}).get("Enabled", False),
                    cooldown_value=data.get("OpeningCooldown", {}).get("Value", 0),
                    permission_required=data.get("Permission_Required", False),
                    hologram=str(data.get("Hologram", "")).replace("\\n", "\n"),
                    hologram_height=float(data.get("HologramHeight", 1.5)),
                    costs=costs,
                    rewards=rewards,
                    locations=data.get("Block", {}).get("Positions", [])
                )
            except Exception as e:
                self.logger.error(f"Failed to load crate {file.name}: {e}")

    def _create_default_crate(self, crates_dir: Path):
        default_crate = {
            "Name": "Default Crate",
            "Description": ["A default crate"],
            "Hologram": "§6§lDefault Crate\n§7Right-click to open",
            "HologramHeight": 1.5,
            "ItemProvider": {"type": "minecraft:chest", "name": "Default Crate"},
            "Preview": {"Enabled": True},
            "Animation": {"Enabled": True},
            "OpeningCooldown": {"Enabled": False, "Value": 0},
            "CostOptions": {
                "key_default": {
                    "required": True,
                    "name": "Default Key",
                    "type": "key",
                    "key_id": "default",
                    "amount": 1
                }
            },
            "Block": {"Positions": []},
            "Rewards": {
                "List": {
                    "diamond": {
                        "Type": "ITEM",
                        "Weight": 50.0,
                        "Rarity": "rare",
                        "PreviewData": {"type": "minecraft:diamond", "amount": 1, "name": "Diamond"},
                        "ItemsData": [{"type": "minecraft:diamond", "amount": 1}]
                    },
                    "coins": {
                        "Type": "COMMAND",
                        "Weight": 50.0,
                        "Rarity": "common",
                        "PreviewData": {"type": "minecraft:gold_ingot", "amount": 1, "name": "100 Coins"},
                        "Commands": ["eco give %player% 100"]
                    }
                }
            }
        }
        save_yaml(crates_dir / "default.yml", default_crate)

    def get_crate(self, crate_id: str) -> Optional[Crate]:
        return self.crates.get(crate_id.lower())

    def get_key(self, key_id: str) -> Optional[CrateKey]:
        return self.keys.get(key_id.lower())
        
    def get_crate_by_location(self, x: float, y: float, z: float, dim: str) -> Optional[Crate]:
        for crate in self.crates.values():
            for loc in crate.locations:
                if loc["x"] == x and loc["y"] == y and loc["z"] == z and loc.get("dim", "") == dim:
                    return crate
        return None

    def save_crate_locations(self, crate: Crate):
        crates_dir = self.data_folder / "crates"
        file = crates_dir / f"{crate.id}.yml"
        data = load_yaml(file)
        if "Block" not in data:
            data["Block"] = {}
        data["Block"]["Positions"] = crate.locations
        save_yaml(file, data)
