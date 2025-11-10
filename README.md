# Candy Bianca - Home Assistant Integration (HACS)

Custom integration for **Candy Bianca** washer/dryer, extracted and refactored
from the original `hm_candy_bianca` package by @wariat85.

This repo is **separate** from the legacy YAML package and is HACS-ready.

## Features

- Read machine status (MachMd)
- Read current program (with mappings for known programs)
- Read remaining time, delay, temperature, spin, steam, dry mode
- Expose raw values (Pr, PrCode, SLevel, etc.)
- Start/Stop program via services:
  - `candy_bianca.start`
  - `candy_bianca.stop`
- Start/Stop buttons as entities:
  - `button.candy_bianca_start`
  - `button.candy_bianca_stop`
- Configure washer IP from UI (Config Flow)
- Configure refresh interval from UI (Options Flow)

## Installation via HACS

1. In HACS go to **Integrations** → menu (⋮) → **Custom repositories**.
2. Add: `https://github.com/wariat85/ha-candy-bianca` as type `Integration`.
3. Search for **Candy Bianca** in HACS and install.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration → Candy Bianca**.
6. Enter:
   - the IP address of your Candy Bianca washer
   - the desired refresh interval (default 30s).

## Usage

- Use the exposed sensors in dashboards and automations.
- Call services:
  - `candy_bianca.start` with:
    - `entity_id` (any entity from this integration)
    - optional `program_url`, `temp`, `spin`, `delay`
  - `candy_bianca.stop` with:
    - `entity_id`
- Or simply click the **Start** / **Stop** buttons created as entities.
