<p align="center">
  <img src="https://raw.githubusercontent.com/wariat85/ha-candy-bianca/main/brands/candy_bianca/logo.jpg" width="320" alt="Candy Bianca Logo">
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
  - `Start Program` / `Stop Program`
- Configure washer IP from UI (Config Flow)
- Configure refresh interval from UI (Options Flow)
- Program presets (Rapid 14/30/44/59, Asciugatura Misti ...) selectable directly in the service or via the new **Program Preset** select entity
- Ready-to-use Lovelace card snippet to drop on your dashboard

## Installation via HACS

1. In HACS go to **Integrations** → menu (⋮) → **Custom repositories**.
2. Add: `https://github.com/wariat85/ha-candy-bianca` as type `Integration`.
3. Search for **Candy Bianca** in HACS and install.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration → Candy Bianca**.
6. Enter:
   - the IP address of your Candy Bianca washer
   - the desired refresh interval (default 30s).

## Usage (examples)

Start a preset:

```yaml
service: candy_bianca.start
data:
  entity_id: sensor.candy_bianca_status
  program_preset: "Perfect Rapid 30 Min."
```

Start with custom string:

```yaml
service: candy_bianca.start
data:
  entity_id: sensor.candy_bianca_status
  program_url: "PrNm=16&PrCode=7&PrStr=Rapido 14 Min.&SLevTgt=1&Dry=0"
```

Stop:

```yaml
service: candy_bianca.stop
data:
  entity_id: sensor.candy_bianca_status
```

Or use the Start/Stop buttons on the device page.

## Default Lovelace card

Want to quickly expose the most useful washer entities on your dashboard? A manual
card configuration is available in [`dashboard/candy_bianca_card.yaml`](dashboard/candy_bianca_card.yaml).

1. Copy the file content.
2. In Home Assistant open your dashboard → **Edit** → **Add card** → **Manual**.
3. Paste the YAML and adjust the entity IDs if your washer isn't called
   `sensor.candy_bianca_*`.
4. Save to get a vertical stack with the status sensors, program select dropdown
   and start/stop buttons.

Feel free to customize the snippet (add pictures, change icons, etc.) to match
your setup.

## Branding

You can replace the placeholder icons in:

- `brands/candy_bianca/icon.png`
- `brands/candy_bianca/logo.png`

with your own artwork.
