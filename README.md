# Privacy Policy for ProMax Bot

**Last Updated:** July 15, 2025

This Privacy Policy explains what information we collect from users of the ProMax bot ("Bot"), how we use it, and how we protect it. Your use of the Bot constitutes your acceptance of this policy.

## 1. What Information Do We Collect?

The Bot is designed to be privacy-focused. We only collect the following information:

*   **User ID:** We store your unique Discord User ID to associate you with your in-game economy data (balance, items, job, etc.).
*   **Server ID:** We store the ID of the servers the Bot is in to provide server-specific features.
*   **In-Game Data:** All data related to your activity within the bot, such as your balance, work history, items purchased, etc., is stored.

**We DO NOT collect or store any personally identifiable information (PII), such as:**

*   Your email address
*   Your passwords
*   Your real name
*   The content of your messages

## 2. How Do We Use Your Information?

The information collected is used exclusively to provide the core functionality of the Bot. For example, your User ID is used to save your money so you don't lose it when you leave and rejoin a server.

## 3. How Do We Protect Your Information?

All collected data is stored on a secure, private server (VPS). We take reasonable measures to protect your data from unauthorized access or disclosure.

## 4. Data Sharing

We do not sell, trade, or otherwise transfer your information to outside parties. All data is for the sole use of the Bot's functionality.

## 5. Data Retention and Deletion

Your data is retained as long as you are using the Bot. If you wish to have your data deleted, you can contact us through the official support server.

## 6. Contact Us
If you have any questions about this Privacy Policy, please join our support server: https://discord.gg/HqxNCtvGum

## CLI Dominos Game

A playable dominos CLI game is available in `src/dominos`.

### Run

```bash
PYTHONPATH=src python -m dominos.main
```

Optional arguments:

```bash
PYTHONPATH=src python -m dominos.main --seed 7 --max-pip 6 --target-score 50
```

### New Features Added

1. **Configurable tileset size** via `--max-pip` (`double-six` by default).
2. **Match mode with cumulative scoring** until `--target-score` is reached.
3. **Save and load game state** from CLI (`S` to save, `L` to load).
4. **Move history viewer** in CLI (`M`) with recent actions.
5. **Round stats tracking** (player/CPU draw counts and score summary each turn).

### Rules Implemented

- Unique tile set generated for `0..max-pip`, shuffled deterministically with optional seed.
- Two players (human + CPU), up to 7 tiles dealt each depending on set size.
- Opening move auto-places the highest double found in either hand, then alternates turns.
- Tile orientation auto-rotates when needed for a valid placement.
- Tiles are legal when either side matches current table ends; legal sides are shown in hand display.
- If no playable tile exists, you can draw one (`D`) or auto-draw until playable (`A`); pass when boneyard is empty.
- CPU chooses the playable tile with highest pip total (double-preferred tie-break), otherwise draws until playable or empty boneyard.
- Win when a hand is empty.
- Blocked game support when both players cannot play and boneyard is empty; winner decided by lowest remaining pip total.

### Known Limitations

- CPU strategy is intentionally simple (highest-pip heuristic with double tie-break).
- Command-line UX is text-only (no GUI).
