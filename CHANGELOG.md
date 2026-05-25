# Changelog

## v1.0.0

### Features
- Animated crate opening with rolling reward display
- Lock mode preview: players can view rewards without taking them
- Edit mode: admins place items directly into chest GUI to configure rewards
- Virtual and physical key support
- Economy cost support via JWEconomy
- Per-crate cooldowns
- Permission-gated crates
- Floating text holograms above crate blocks
- Configurable messages via `messages.yml` with `&` color codes
- Reward names auto-resolved from item display name or type ID
- Paginated preview menu with next/prev navigation
- Enchantment display in preview and opening animations
- Crate block interaction (right-click to open, shift+right-click to preview)
- Admin block break removes crate location
- Default crate and key configs generated on first run

### Technical
- Uses JWInventoryAPI v3.0.0 lock mode for exploit-proof preview/opening
- Uses JWInventoryAPI edit mode for reward editing
- Animation uses batch mode + `refresh_contents()` for smooth rolling without client crashes
- Reward winner is determined by center slot position when animation stops
- SQLite database for virtual keys and cooldowns
- YAML config loader with deep merge defaults
