# JWCrate

**JWCrate** is a full-featured crate system for Endstone Bedrock servers with animated openings, configurable rewards, virtual/physical keys, economy integration, and floating holograms. Inspired by ExcellentCrates.

### What does it do?
It lets you create crates that players can open with keys or currency. Each crate has configurable rewards with weighted chances, animated rolling displays, and preview menus. Admins can edit rewards directly in-game by placing items into a chest GUI.

### Why is it useful?
- **For Server Owners:** Fully configurable crate system with YAML configs, in-game editing, hologram displays, and customizable messages. No coding required to set up new crates.
- **For Players:** Smooth animated crate openings, preview rewards before opening, and clear feedback on what they won.

### How to use it?
Install both JWCrate and JWInventoryAPI wheels in your server's `plugins/` directory. On first run, default configs are generated. Customize crates in `data/crates/`, keys in `data/keys/`, and messages in `data/messages.yml`.

## Features

- **Animated Opening:** Rolling reward display in a chest GUI with smooth animation
- **Lock Mode Preview:** Players can browse rewards without taking them
- **In-Game Editing:** Admins place items directly into a chest GUI to configure rewards (preserves enchants, lore, NBT)
- **Virtual & Physical Keys:** Keys can be database-tracked (virtual) or real items in inventory
- **Economy Costs:** Charge currency via JWEconomy instead of (or in addition to) keys
- **Per-Crate Cooldowns:** Prevent spam-opening with configurable cooldown timers
- **Permission Gates:** Restrict crate access to specific permission groups
- **Floating Holograms:** Client-side text entities above crate blocks
- **Configurable Messages:** All player-facing text in `messages.yml` with `&` color codes
- **Smart Reward Names:** Auto-resolved from item display name or type ID

## Commands & Permissions

| Command | Permission | Description |
|---------|------------|-------------|
| `/jwcrate reload` | `jwcrate.command.reload` | Reload all configs |
| `/jwcrate give <player> <crate> [amount]` | `jwcrate.command.give` | Give physical crate item |
| `/jwcrate keygive <player> <key> [amount]` | `jwcrate.command.key.give` | Give key (virtual or physical) |
| `/jwcrate open <crate>` | - | Open crate virtually |
| `/jwcrate preview <crate>` | - | Preview crate rewards |
| `/jwcrate edit <crate>` | `jwcrate.admin` | Edit rewards in chest GUI |
| `/jwcrate set <crate>` | `jwcrate.command.set` | Set crate block location |

Aliases: `/crate`, `/crates`

## Crate Interaction

- **Right-click** crate block → open crate (deducts key/cost)
- **Shift + right-click** crate block → preview rewards
- **Break** crate block (admin only) → removes crate location

## Configuration

### Crate Config (`data/crates/<id>.yml`)

```yaml
Name: "Example Crate"
Description: ["A cool crate"]
Hologram: "§6§lExample Crate\n§7Right-click to open"
HologramHeight: 1.5
ItemProvider:
  type: "minecraft:chest"
  name: "Example Crate"
Preview:
  Enabled: true
Animation:
  Enabled: true
OpeningCooldown:
  Enabled: false
  Value: 0
Permission_Required: false
CostOptions:
  key_default:
    required: true
    name: "Default Key"
    type: key
    key_id: default
    amount: 1
Block:
  Positions: []
Rewards:
  List:
    diamond:
      Name: "Diamond"
      Type: ITEM
      Weight: 50.0
      Rarity: rare
      PreviewData:
        type: "minecraft:diamond"
        amount: 1
        name: "Diamond"
      ItemsData:
        - type: "minecraft:diamond"
          amount: 1
    coins:
      Name: "100 Coins"
      Type: COMMAND
      Weight: 50.0
      Rarity: common
      PreviewData:
        type: "minecraft:gold_ingot"
        amount: 1
        name: "100 Coins"
      Commands:
        - "eco give %player% 100"
```

### Key Config (`data/keys/<id>.yml`)

```yaml
Name: "Default Key"
Virtual: false
ItemData:
  type: "minecraft:tripwire_hook"
  name: "Default Key"
```

### Messages (`data/messages.yml`)

All player-facing messages are configurable with `&` color codes. Generated on first run with sensible defaults. Example:

```yaml
reward_win: "&aYou won &f{reward}&a!"
reward_broadcast: "&6{player} won &f{reward}&6 from {crate}!"
cannot_afford: "&cYou cannot afford to open this crate."
cooldown: "&cCrate is on cooldown for {seconds}s."
```

## Reward Naming

Rewards display proper names in win/broadcast messages. Priority:

1. Explicit `Name` field in reward config
2. `name` field from `PreviewData`
3. Auto-derived from item type (e.g. `minecraft:diamond_sword` → `Diamond Sword`)

## Reward Types

### ITEM
Gives physical items to the player. Supports custom name, lore, enchantments, unbreakable flag.

### COMMAND
Executes server commands. Supports `%player%` placeholder (and JWPlaceholderAPI if installed).

## Installation

Place both wheels in your server's `plugins/` directory:

```
endstone_jwinventoryapi-2.0.0-py2.py3-none-any.whl
endstone_jwcrate-1.0.0-py3-none-any.whl
```

## Dependencies

- endstone
- JWInventoryAPI (required)
- JWEconomy (optional, for economy costs)
- JWPlaceholderAPI (optional, for command placeholders)
- PyYAML
