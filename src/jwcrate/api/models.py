from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class Reward:
    id: str
    name: str
    type: str
    weight: float
    rarity: str
    preview: Dict[str, Any]
    items: List[Dict[str, Any]] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    broadcast: bool = False


@dataclass
class CrateCost:
    id: str
    required: bool
    name: str
    cost_type: str
    currency_id: Optional[str] = None
    key_id: Optional[str] = None
    amount: float = 1.0


@dataclass
class Crate:
    id: str
    name: str
    description: List[str]
    item: Dict[str, Any]
    preview_enabled: bool = True
    opening_enabled: bool = True
    cooldown_enabled: bool = False
    cooldown_value: int = 0
    permission_required: bool = False
    hologram: str = ""
    hologram_height: float = 1.5
    costs: Dict[str, CrateCost] = field(default_factory=dict)
    rewards: Dict[str, Reward] = field(default_factory=dict)
    locations: List[Dict[str, float]] = field(default_factory=list)


@dataclass
class CrateKey:
    id: str
    name: str
    virtual: bool = False
    item: Dict[str, Any] = field(default_factory=dict)
