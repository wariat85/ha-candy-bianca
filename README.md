# Candy Bianca - Home Assistant Integration (HACS)

Custom integration for **Candy Bianca** washer/dryer, extracted and refactored
from the original `hm_candy_bianca` package by @wariat85.

This repo is meant to be **separate** from the legacy package repo and HACS-ready.

## Features

- Read machine status (MachMd)
- Read current program (with mappings for known programs)
- Read remaining time, delay, temperature, spin, steam, dry mode
- Expose raw values (Pr, PrCode, SLevel, etc.)
- Start program via `candy_bianca.start` service
- Stop program via `candy_bianca.stop` service
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

## Services

### `candy_bianca.start`

Parameters:
- `entity_id` (required): any entity from this integration
- `program_url` (optional): full program string (e.g. `PrNm=16&PrCode=7&PrStr=Rapido 14 Min.&SLevTgt=1&Dry=0`)
- `temp` (optional): target temperature
- `spin` (optional): spin setting
- `delay` (optional): delay start (hours)

### `candy_bianca.stop`

Parameters:
- `entity_id` (required): any entity from this integration

## Notes

- Program mappings are based on reverse-engineering and currently cover a subset
  of programs. Unknown combinations are exposed as `Other`, along with raw fields
  to help extending mappings.
