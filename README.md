<p align="center">
  <img src="https://raw.githubusercontent.com/wariat85/ha-candy-bianca/main/brands/candy_bianca/logo.png" width="320" alt="Candy Bianca Logo">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration">
    <img src="https://img.shields.io/badge/HACS-Custom-blue.svg?style=for-the-badge">
  </a>
  <a href="https://github.com/wariat85/ha-candy-bianca/releases">
    <img src="https://img.shields.io/github/v/release/wariat85/ha-candy-bianca?style=for-the-badge">
  </a>
</p>

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

Use the sensors in dashboards and automations, the dedicated start/stop services,
or the Start/Stop buttons on the device page.

## Branding

You can replace the placeholder icons in:

- `brands/candy_bianca/icon.png` (square icon)
- `brands/candy_bianca/logo.png` (horizontal logo)

with your own artwork (Candy-blue washer icon, etc.).
